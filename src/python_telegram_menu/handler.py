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
from typing import Any, List, Optional, Type, Union

import telegram.ext
import validators
from apscheduler.schedulers.base import BaseScheduler
from telegram import Message, ReplyKeyboardMarkup
from telegram import Bot, Chat, ChatAction, InlineKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import CallbackQueryHandler, CommandHandler
from telegram.ext import Dispatcher, MessageHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.parsemode import ParseMode
from telegram.update import Update
from telegram.utils.request import Request

from ._version import __raw_url__
from .core import TypeCallback, emoji_replace
from .core import ABCMessage, Button, ButtonTypes

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
    def filter_unicode(
            string: str
    ) -> str:
        """
        Remove non-unicode characters.
        """
        return string.encode("ascii", "ignore").decode("utf-8")

    @staticmethod
    def _message_check_changes(
            message: ABCMessage,
            content: str
    ) -> bool:
        """
        Check is message content and keyboard has changed since last edit.
        """
        cnt_identical = content == message.content_previous
        kb_identical = [y.label for x in message.keyboard_previous
                        for y in x] == \
                       [y.label for  x in message.keyboard for y in x]

        if cnt_identical and kb_identical :
            return False

        message.content_previous = content
        message.keyboard_previous = message.keyboard.copy()
        return True

    def _expiry_date_checker(
            self
    ) -> None:
        """
        Check expiry message date abd delete on expired.
        """
        for message in self._message_queue:
            if message.is_expired():
                self._delete_queued_message(message)

        if len(self._menu_queue) >= 2 and \
                self._menu_queue[-1].is_expired():
            self.goto_home()

    def delete_message(
            self,
            message_id: int
    ) -> None:
        """
        Delete message by id
        """
        self._bot.delete_message(chat_id=self.chat_id,
                                 message_id=message_id)

    def _delete_queued_message(
            self,
            message: ABCMessage
    ) -> None:
        """
        Delete and remove message from queue
        """
        message.kill_message()
        if message in self._message_queue:
            self.delete_message(message.message_id)
        del message

    def goto_menu(
            self,
            message: ABCMessage
    ) -> int:
        """
        Send and add message to queue
        """
        content = message.update()

        logger.info(f"Opening menu {message.label}")

        keyboard = message.gen_keyboard_content(inlined=False)

        mes = self.send_massage(emoji_replace(content),
                                keyboard,
                                notification=message.notification)

        message.init_date_time()
        self._menu_queue.append(message)
        return mes.message_id

    def goto_home(
            self
    ) -> int:
        """
        Returns to home menu.
        Clear menu_queue
        """
        if len(self._menu_queue) == 1:
            return self._menu_queue[0].message_id  # we are already at home

        previous = self._menu_queue.pop()

        while self._menu_queue:
            previous = self._menu_queue.pop()

        return self.goto_menu(previous)

    def _send_app_message(
            self,
            message: ABCMessage,
            label: str
    ) -> int:
        """
        Send app message
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
            keyboard: Optional[Union[ReplyKeyboardMarkup,
                                     InlineKeyboardMarkup]] = None,
            noification: bool = True
    ) -> telegram.Message:
        """
        Send text message with HTML formatting.
        """
        return self._bot.send_message(
            chat_id=self.chat_id,
            text=content,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_notification=not noification
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
                reply_markup=Keyboard_format
            )
        except telegram.error.BadRequest as error:
            logger.error(error)
            return False
        return True

    def select_menu_button(
            self,
            label: str
    ) ->Optional[int]:
        """
        Menu button by label.
        """
        msg_id = 0
        if label == "Back":
            if len(self._menu_queue) == 1:
                return self._menu_queue[0].message_id  # we are already at home
            previous = self._menu_queue.pop() # delete actual menu
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
                    callback() # execute method
                return msg_id

        # label does not match any sub-menu
        # just process user input
        self.capture_use_input(label)
        return None

    def capture_user_input(
            self,
            label: str
    ) -> None:
        """
        Process user input in last message updated
        """
        last_menu_message = self._menu_queue[-1]
        if self._message_queue:
            last_app_message = self._message_queue[-1]
            if last_app_message.date_time > last_menu_message.date_time:
                last_menu_message = last_app_message
        last_menu_message.text_input(label)
