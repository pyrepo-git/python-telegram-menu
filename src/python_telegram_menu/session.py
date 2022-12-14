#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""
Activate telegram bot session.
"""

import logging
from typing import Any, List, Optional, Type

import telegram.ext
from telegram import Bot
from telegram.error import Unauthorized
from telegram.ext import CallbackQueryHandler, CommandHandler
from telegram.ext import Dispatcher, MessageHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from .core import ABCMessage
from .handler import Handler

logger = logging.getLogger(__name__)


class Session:
    """
    Telegram session.
    Send start message to each new user connecting to the bot.

    Class members:
        - updater:
        - _tg_key: bot telegram key
        - sessions: connection sessions container
        - message: message class
        - message_args: message class args
        - handler: handler class
    """

    TIMEOUT_READ = 5
    TIMEOUT_CONNECT = TIMEOUT_READ
    INIT_STRING = "start"
    BROADCAST_STRING = "broadcast"

    def __init__(
        self,
        tg_key: str,
        start_message: str = INIT_STRING,
        broadcast_string: str = BROADCAST_STRING,
    ) -> None:
        """
        Session object constructor.

        Parameters:
            - tg_key: Telegram bot API key
            - start_message: for init session message
            - broadcast_string: for broadcast session message
        """
        if not isinstance(tg_key, str):
            raise KeyError("Telegram API Key must be a string.")

        self.updater = telegram.ext.Updater(
            tg_key,
            use_context=True,
            request_kwargs={
                "read_timeout": self.TIMEOUT_READ,
                "connection_timeout": self.TIMEOUT_CONNECT,
            },
        )

        bot: Bot = self.updater.bot
        dispatcher: Dispatcher = self.updater.dispatcher
        self.scheduler = self.updater.job_queue.scheduler

        try:
            logger.info(
                f"Connected to Telegram bot {bot.name}({bot.first_name})"
            )
        except Unauthorized as error:
            raise AttributeError(
                f"Bot matching by key {tg_key} not found."
            ) from error

        self._tg_key = tg_key
        self.sessions: List[Handler] = []
        self.start_message_class: Optional[Type[ABCMessage]] = None
        self.start_message_args: Optional[List[Any]] = None
        self.navigation_handler_class: Optional[Type["Handler"]] = None

        # add command handlers
        dispatcher.add_handler(
            CommandHandler(start_message, self._on_start_message)
        )

        dispatcher.add_handler(
            CommandHandler(broadcast_string, self._on_start_message)
        )

        dispatcher.add_handler(
            MessageHandler(telegram.ext.Filters.text, self._on_button_callback)
        )

        dispatcher.add_handler(
            MessageHandler(
                telegram.ext.Filters.status_update.web_app_data,
                self._on_web_callback,
            )
        )

        dispatcher.add_handler(CallbackQueryHandler(self._on_inline_callback))

        dispatcher.add_handler(
            telegram.ext.PollAnswerHandler(self._on_poll_answer)
        )

        dispatcher.add_error_handler(self._on_error)

    def start(
        self,
        start_message: Type[ABCMessage],
        start_message_args: Optional[List[Any]] = None,
        polling: bool = True,
        idle: bool = False,
        navigation_handler_class: Optional[Type["Handler"]] = None,
    ) -> None:
        """
        Activate scheduler and dispatcher.

        Parameters:
            - message: class used to create message
            - message_args: optional message class args
            - polling: if True - start polling updates from telegram
            - idle: if True - blocks until one of the signals are
              received and stops the updater
            - handler_class: optional class extended base handler class
        """
        self.start_message_class = start_message
        self.start_message_args = start_message_args
        self.navigation_handler_class = navigation_handler_class

        if not issubclass(start_message, ABCMessage):
            raise AttributeError("message must be ABCMessage type!")
        if start_message_args is not None and not isinstance(
            start_message_args, list
        ):
            raise AttributeError("message_args is not a list!")
        if not issubclass(self.navigation_handler_class, Handler):
            raise AttributeError("handler must be a Handler type!")

        if not self.scheduler.running:
            self.scheduler.start()
        if polling:
            self.updater.start_polling()
        if idle:
            self.updater.idle()

    def _on_start_message(self, update: Update, _: CallbackContext) -> None:
        """
        Start bot telegram session.
        """
        chat = update.effective_chat

        if chat is None:
            raise AttributeError("Error! Chat object not exist.")
        if self.navigation_handler_class is None:
            raise AttributeError("Error! Handler class not defined.")

        session = self.navigation_handler_class(
            self._tg_key, chat, self.scheduler
        )
        self.sessions.append(session)

        if self.start_message_class is None:
            raise AttributeError("Error! Message class not defined.")
        if self.start_message_args is not None:
            start_message = self.start_message_class(
                session, message_args=self.start_message_args
            )
        else:
            start_message = self.start_message_class(session)

        session.goto_menu(start_message)

    def get_session(self, chat_id: int = 0) -> Optional["Handler"]:
        """
        Get session by chat_id.
        """
        sessions = [x for x in self.sessions if chat_id in (x.chat_id, 0)]
        if not sessions:
            return None
        return sessions[0]

    def _on_web_callback(self, update: Update, context: Any) -> None:
        """
        Callback for webapp results
        """
        if update.effective_chat is None or update.effective_message is None:
            raise AttributeError("Error! Chat or Message object nut found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._on_start_message(update, context)
            return

        session.app_message_webapp_callback(
            update.effective_message.web_app_data.data,
            update.effective_message.web_app_data.button_text,
        )

    def _on_button_callback(
        self, update: Update, context: CallbackContext
    ) -> None:
        """
        Select menu item
        """
        if update.effective_chat is None:
            raise AttributeError("Error! Chat object not found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._on_start_message(update, context)
            return

        session.select_menu_button(update.message.text)

    def _on_poll_answer(self, update: Update, _: CallbackContext) -> None:
        """
        Poll message for user session.
        """
        if update.effective_user is None:
            raise AttributeError("Error! user object not found.")

        session = next(
            (
                x
                for x in self.sessions
                if x.user_name == update.effective_user.first_name
            ),
            None,
        )

        if session:
            session.poll_answer(update.poll_answer.option_ids[0])

    def _on_inline_callback(
        self, update: Update, context: CallbackContext
    ) -> None:
        """
        Select and execute inline callback.
        """
        if update.effective_chat is None:
            raise AttributeError("Error! Chat object not found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._on_start_message(update, context)
            return

        session.app_message_button_callback(
            update.callback_query.data, update.callback_query.id
        )

    def _on_broadcast_message(
        self, message: str, notification: bool = True
    ) -> List[telegram.Message]:
        """
        Broadcast messages for all sessions.
        """
        messages = []
        for session in self.sessions:
            mes = session.send_message(message, notification=notification)
            if mes is not None:
                messages.append(mes)
        return messages

    def _on_broadcast_picture(
        self, picture_path: str, notification: bool = True
    ) -> List[telegram.Message]:
        """
        Broadcast picture messages.
        """
        messages = []
        for session in self.sessions:
            mes = session.send_photo(picture_path, notification=notification)
            if mes is not None:
                messages.append(mes)
        return messages

    def _on_broadcast_sticker(
        self, sticker_path: str, notification: bool = True
    ) -> List[telegram.Message]:
        """
        Broadcast sticker messages.
        """
        messages = []
        for session in self.sessions:
            mes = session.send_sticker(sticker_path, notification=notification)
            if mes is not None:
                messages.append(mes)
        return messages

    @staticmethod
    def _on_error(update: object, context: CallbackContext) -> None:
        """
        Log error
        """
        if not isinstance(update, Update):
            raise AttributeError("Incorrect update object")

        error = (
            str(context.error)
            if update is None
            else f"Update {update.update_id} - {str(context.error)}"
        )
        logger.error(error)
