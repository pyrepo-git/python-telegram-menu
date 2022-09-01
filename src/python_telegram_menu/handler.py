#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""
Handler for telegram bot session.
"""

import datetime
import imghdr
import logging
import mimetypes
import time
from pathlib import Path
from typing import List, Optional, Union

import telegram.ext
import validators
from apscheduler.schedulers.base import BaseScheduler
from telegram import Bot, Chat, ChatAction, InlineKeyboardMarkup
from telegram import Message, ReplyKeyboardMarkup
from telegram.parsemode import ParseMode
from telegram.utils.request import Request

from ._version import __raw_url__
from .core import ABCMessage, ButtonTypes
from .core import TypeCallback, emoji_replace

logger = logging.getLogger(__name__)


class Handler:
    """
    Handle requests telegram bot requests.
    """
    POLL_DEALING = 10  # seconds
    MESSAGE_CHECK_TIMEOUT = POLL_DEALING
    CONNECTION_POOL_SIZE = 8

    def __init__(
            self,
            tg_key: str,
            chat: Chat,
            scheduler: BaseScheduler
    ) -> None:
        """
        Handler class initialization.

        Parameters:
            - tg_key:
            - chat:
            - scheduler:
        """
        request = Request(con_pool_size=self.CONNECTION_POOL_SIZE)
        self._bot = Bot(token=tg_key, request=request)
        self._poll: Optional[Message] = None
        self._poll_callback: Optional[TypeCallback] = None
        self.scheduler = scheduler
        self.chat_id = chat.id
        self.user_name = chat.first_name
        self.poll_name = f"poll_{self.user_name}"

        logger.info(f"Opening chat with user {self.user_name}")

        self._menu_queue: List[ABCMessage] = []  # user selected menus
        self._message_queue: List[ABCMessage] = []  # app messages sent

        scheduler.add_job(
            self._expiry_date_checker,
            "interval",
            id="state_nav_update",
            seconds=self.MESSAGE_CHECK_TIMEOUT,
            replace_existing=True,
        )

    @staticmethod
    def filter_unicode(string: str) -> str:
        """
        Remove non-unicode characters.
        """
        return string.encode("ascii", "ignore").decode("utf-8")

    @staticmethod
    def _message_check_changes(message: ABCMessage, content: str) -> bool:
        """
        Check is message content and keyboard has changed since last edit.
        """
        cnt_identical = content == message.content_previous
        kb_identical = [
            y.label for x in message.keyboard_previous for y in x
        ] == [y.label for x in message.keyboard for y in x]

        if cnt_identical and kb_identical:
            return False

        message.content_previous = content
        message.keyboard_previous = message.keyboard.copy()
        return True

    @staticmethod
    def _sticker_check_replace(sticker_path: str) -> Union[str, bytes]:
        """
        Check correctness sticker path.
        If not replace be default.
        """
        try:
            if not sticker_path.lower().endswith(".webp"):
                raise ValueError("Sticker has no .webp format")
            if validators.url(sticker_path):
                return sticker_path  # todo: add check if url exist
            if Path(sticker_path).is_file() and imghdr.what(sticker_path):
                with open(sticker_path, "rb") as file_h:
                    return file_h.read()
            raise ValueError("Pats is not a picture")
        except ValueError:
            url_default = f"{__raw_url__}/resources/stats_default.webp"
            logger.error(
                f"Picture path '{sticker_path}' not valid."
                f"Replaced by default {url_default}"
            )
            return url_default

    @staticmethod
    def _picture_check_replace(picture_path: str) -> Union[str, bytes]:
        """
        Check correctness picture path.
        If not replace be default.
        """
        try:
            if validators.url(picture_path):
                # check if the url has image format
                mimetype, _ = mimetypes.guess_type(picture_path)
                if mimetype and mimetype.startswith("image"):
                    return picture_path
                raise ValueError("Url is not a picture")

            if Path(picture_path).is_file() and imghdr.what(picture_path):
                with open(picture_path, "rb") as file_h:
                    return file_h.read()

            raise ValueError("Url not picture path")

        except ValueError:
            url_default = f"{__raw_url__}/resources/stats_default.png"
            logger.error(
                f"Picture path '{picture_path}' invalid."
                f"Replaced by default {url_default}"
            )
            return url_default

    def _expiry_date_checker(self) -> None:
        """
        Check expiry message date abd delete on expired.
        """
        for message in self._message_queue:
            if message.is_expired():
                self._delete_queued_message(message)

        if len(self._menu_queue) >= 2 and self._menu_queue[-1].is_expired():
            self.goto_home()

    def delete_message(self, message_id: int) -> None:
        """
        Delete telegram message by id.
        """
        self._bot.delete_message(chat_id=self.chat_id, message_id=message_id)

    def _delete_queued_message(self, message: ABCMessage) -> None:
        """
        Delete and remove message from queue.
        """
        message.kill_message()
        if message in self._message_queue:
            self.delete_message(message.message_id)
        del message

    def goto_menu(self, message: ABCMessage) -> int:
        """
        Send and add message to queue.
        """
        content = message.update()

        logger.info(f"Opening menu {message.label}")

        keyboard = message.gen_keyboard_content(inlined=False)

        mes = self.send_message(
            emoji_replace(content), keyboard, notification=message.notification
        )

        message.init_date_time()
        self._menu_queue.append(message)
        return mes.message_id

    def goto_home(self) -> int:
        """
        Returns to home menu.
        Clear menu_queue.
        """
        if len(self._menu_queue) == 1:
            return self._menu_queue[0].message_id  # we are already at home

        previous = self._menu_queue.pop()

        while self._menu_queue:
            previous = self._menu_queue.pop()

        return self.goto_menu(previous)

    def _send_app_message(
            self, message: ABCMessage, label: str
    ) -> int:
        """
        Send app message.
        """
        content = emoji_replace(message.update())

        info = self.filter_unicode(f"Send message '{message.label}':'{label}'")
        logger.info(str(info))

        if "_" not in message.label:
            message.label = f"{message.label}_{label}"

        exist = self.get_message(message.label)
        if exist is not None:
            self._delete_queued_message(message)

        message.init_date_time()
        keyboard = message.gen_keyboard_content(inlined=True)
        mes = self.send_message(content, keyboard, message.notification)
        message.message_id = mes.message_id
        self._message_queue.append(message)

        message.content_previous = content
        message.keyboard_previous = message.keyboard.copy()
        return message.message_id

    def send_message(
            self,
            content: str,
            keyboard: Optional[
                Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]
            ] = None,
            notification: bool = True
    ) -> telegram.Message:
        """
        Send text message with HTML formatting.
        """
        return self._bot.send_message(
            chat_id=self.chat_id,
            text=content,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_notification=not notification
        )

    def edit_message(
            self,
            message: ABCMessage
    ) -> bool:
        """
        Edit inline message asynchronously.
        """
        mes = self.get_message(message.label)
        if mes is None:
            return False

        content = emoji_replace(mes.update())
        if not self._message_check_changes(mes, content):
            return False

        keyboard_format = mes.gen_keyboard_content()

        try:
            self._bot.edit_message_text(
                text=content,
                chart_id=self.chat_id,
                message_id=mes.message_id,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_format
            )
        except telegram.error.BadRequest as error:
            logger.error(error)
            return False
        return True

    def select_menu_button(self, label: str) -> Optional[int]:
        """
        Menu button by label.
        """
        msg_id = 0
        if label == "Back":
            if len(self._menu_queue) == 1:
                return self._menu_queue[0].message_id  # we are already at home
            previous = self._menu_queue.pop()  # delete actual menu
            if self._menu_queue:
                previous = self._menu_queue.pop()
            return self.goto_menu(previous)

        if label == "Home":
            return self.goto_home()

        for item in self._menu_queue[::-1]:
            btn_found = item.get_button(label)
            if btn_found:
                callback = btn_found.callback
                if isinstance(callback, ABCMessage):
                    if callback.inlined:
                        msg_id = self._send_app_message(callback, label)
                        if callback.home_after:
                            msg_id = self.goto_home()
                    else:
                        msg_id = self.goto_menu(callback)
                elif callback is not None and hasattr(callback, "__call__"):
                    callback()  # execute method
                return msg_id

        # label does not match any sub-menu
        # just process user input
        self.capture_user_input(label)
        return None

    def capture_user_input(self, label: str) -> None:
        """
        Process user input in last message updated.
        """
        last_menu_message = self._menu_queue[-1]
        if self._message_queue:
            last_app_message = self._message_queue[-1]
            if last_app_message.date_time > last_menu_message.date_time:
                last_menu_message = last_app_message
        last_menu_message.text_input(label)

    def app_message_webapp_callback(
        self, webapp_data: str, button_text: str
    ) -> None:
        """
        Execute web app callback.
        """
        last_menu = self._menu_queue[-1]
        webapp_message = next(iter(y for x in last_menu.keyboard
                                   for y in x if y.label == button_text), None)
        if webapp_message is not None and callable(webapp_message.callback):
            html_response = webapp_message.callback(webapp_data)
            self.send_message(html_response,
                              notification=webapp_message.notification)

    def app_message_button_callback(
            self,
            callback_label: str,
            callback_id: str
    ) -> None:
        """
        Execute action after message button selected.
        """
        label_message, label_action = callback_label.split(".")
        log_message = \
            self.filter_unicode(f"Received action request from "
                                f"'{label_message}':'{label_action}'")
        logger.info(log_message)

        message = self.get_message(label_message)
        if message is None:
            logger.error(f"Message with label {label_message} not found")
            return

        bt_found = message.get_button(label_action)
        if bt_found is None:
            logger.error(f"Button with label {label_action} not found")
            return

        if bt_found.button_type in [ButtonTypes.PICTURE, ButtonTypes.STICKER]:
            self._bot.send_chat_action(chat_id=self.chat_id,
                                       action=ChatAction.UPLOAD_PHOTO)
        elif bt_found.button_type == ButtonTypes.MESSAGE:
            self._bot.send_chat_action(chat_id=self.chat_id,
                                       action=ChatAction.TYPING)
        elif bt_found.button_type == ButtonTypes.POLL:
            self.send_poll(question=bt_found.args[0],
                           options=bt_found.args[1])
            self._poll_callback = bt_found.callback
            self._bot.answer_callback_query(callback_id,
                                            text="Select an answer...")
            return

        if bt_found.args is not None:
            action_status = bt_found.callback(bt_found.args)
        else:
            action_status = bt_found.callback()

        # send picture if custom label found
        if bt_found.button_type == ButtonTypes.PICTURE:
            self.send_photo(picture_path=action_status,
                            notification=bt_found.notification)
            self._bot.answer_callback_query(callback_id, text="Picture sent!")
            return
        if bt_found.button_type == ButtonTypes.STICKER:
            self.send_sticker(sticker_path=action_status,
                              notification=bt_found.notification)
            self._bot.answer_callback_query(callback_id, text="Sticker sent!")
            return
        if bt_found.button_type == ButtonTypes.MESSAGE:
            self.send_message(action_status,
                              notification=bt_found.notification)
            self._bot.answer_callback_query(callback_id, text="Message sent!")
            return
        self._bot.answer_callback_query(callback_id, text=action_status)

        # update expiry period and update
        message.init_date_time()
        self.edit_message(message)

    def send_photo(
            self,
            picture_path: str,
            notification: bool = True
    ) -> Optional[telegram.Message]:
        """
        Send picture.
        """
        picture_object = self._picture_check_replace(picture_path=picture_path)
        try:
            return self._bot.send_photo(chat_id=self.chat_id,
                                        photo=picture_object,
                                        disable_notification=not notification)
        except telegram.error.BadRequest as error:
            logger.error(f"Failed send picture {picture_path}:{error}")

        return None

    def send_sticker(
            self,
            sticker_path: str,
            notification: bool = True
    ) -> Optional[telegram.Message]:
        """
        Send sticker.
        """
        sticker_object = self._sticker_check_replace(sticker_path=sticker_path)
        try:
            return self._bot.send_sticker(chat_id=self.chat_id,
                                          sticker=sticker_object,
                                          disable_notification=not notification
                                          )
        except telegram.error.BadRequest as error:
            logger.error(f"failed send sticker {sticker_path}:{error}")

        return None

    def get_message(
            self,
            label: str
    ) -> Optional[ABCMessage]:
        """
        Get message from message queue by attribute label.
        """
        return next(iter(x for x in self._message_queue
                         if x.label == label), None)

    def send_poll(
            self,
            question: str,
            options: List[str]
    ) -> None:
        """
        Send poll to user with questions and options.
        """
        if self.scheduler.get_job(self.poll_name) is not None:
            self.poll_delete()

        options = [emoji_replace(x) for x in options]
        self._poll = self._bot.send_poll(
            chat_id=self.chat_id,
            question=emoji_replace(question),
            options=options,
            is_anonymous=False,
            open_period=self.POLL_DEALING
        )

        next_time = datetime.datetime.now()
        next_time += datetime.timedelta(seconds=self.POLL_DEALING + 1)

        self.scheduler.add_job(
            self.poll_delete,
            "date",
            id=self.poll_name,
            next_run_time=next_time,
            replace_existing=True
        )

    def poll_delete(
            self
    ) -> None:
        """
        On poll timeout expired.
        """
        if self._poll is not None:
            try:
                logger.info(f"Deleting poll '{self._poll.poll.question}'")
                self._bot.delete_message(
                    chat_id=self.chat_id,
                    message_id=self._poll.message_id
                )
            except telegram.error.BadRequest:
                logger.error(f"Poll message {self._poll.message_id} "
                             f"already deleted")

    def poll_answer(
            self,
            answer_id: int
    ) -> None:
        """
        Run when received poll message.
        """
        if self._poll is None or self._poll_callback is None or not \
                callable(self._poll_callback):
            logger.error("Poll not defined")
            return

        answer_ascii = self._poll.poll.options[answer_id].text
        answer_ascii.encode("ascii", "ignore").decode()

        logger.info(f"{self.user_name}'s answer to question "
                    f"'{self._poll.poll.question}' is '{answer_ascii}'")

        self._poll_callback(self._poll.poll.options[answer_id].text)
        time.sleep(1)
        self.poll_delete()

        if self.scheduler.get_job(self.poll_name) is not None:
            self.scheduler.remove_job(self.poll_name)

        self._poll = None
