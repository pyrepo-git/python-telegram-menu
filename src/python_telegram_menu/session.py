#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""
Activate telegram bot session.
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
from .handler import NavigationHandler

logger = logging.getLogger(__name__)


class Session:
    """
    Telegram session.
    Send start message to each new user connecting to the bot.

    Class members:
        - updater:
    """
    TIMEOUT_READ = 5
    TIMEOUT_CONNECT = TIMEOUT_READ
    INIT_MESSAGE = "start"

    def __init__(
            self,
            tg_key: str,
            init_message: str = INIT_MESSAGE
    ) -> None:
        """
        Session object constructor.

        Parameters:
            - tg_key: Telegram bot API key
            - init_message: init session message
        """
        if not isinstance(tg_key, str):
            raise KeyError("Telegram API Key must be a string.")

        self.updater = telegram.ext.Updater(
            tg_key,
            use_context=True,
            request_kwargs={"read_timeout": self.TIMEOUT_READ,
                            "connection_timeout": self.TIMEOUT_CONNECT}
        )

        bot: Bot = self.updater.bot
        dispatcher: Dispatcher = self.updater.dispatcher
        self.scheduler = self.updater.job_queue.scheduler

        try:
            logger.info(f"Connected to Telegram bot {bot.name}({bot.first_name})")
        except Unauthorized as error:
            raise AttributeError(f"Bot matching by key {tg_key} not found.") from error

        self._tg_key = tg_key
        self.sessions: List[NavigationHandler] = []
        self.start_message_class: Optional[Type[ABCMessage]] = None
        self.start_message_args: Optional[List[Any]] = None
        self.navigation_handler_class: Optional[Type["NavigationHandler"]] = None

        # add command handlers
        dispatcher.add_handler(CommandHandler(init_message, self._send_start_message_))
        dispatcher.add_handler(MessageHandler(telegram.ext.Filters.text,
                                              self._button_select_callback))
        dispatcher.add_handler(MessageHandler(telegram.ext.Filters.status_update.web_app_data,
                                              self._web_app_callback))
        dispatcher.add_handler((CallbackQueryHandler(self._button_inline_select_callback)))
        dispatcher.add_handler(telegram.ext.PollAnswerHandler(self._poll_answer))
        dispatcher.add_error_handler(self._msg_error_handler)

    def start(
            self,
            start_message_class: Type[ABCMessage],
            start_message_args: Optional[List[Any]] = None,
            polling: bool = True,
            idle: bool = False,
            navigation_handler_class: Optional[Type["NavigationHandler"]] = None
    ) -> None:
        """
        Activate scheduler and dispatcher.

        Parameters:
            - start_message_class: class used to create start message
            - start_message_args: optional arguments passed to start class
            - polling: if True - start polling updates from telegram
            - idle: if True - blocks until one of the signals are received and stops the updater
            - navigation_handler_class: optional class extended base navigation handler
        """
        self.start_message_class = start_message_class
        self.start_message_args = start_message_args
        self.navigation_handler_class = navigation_handler_class

        if not issubclass(start_message_class, ABCMessage):
            raise AttributeError("start_message_class must be ABCMessage!")
        if start_message_args is not None and not isinstance(start_message_args, list):
            raise AttributeError("start_message_args is not a lis!")
        if not issubclass(self.navigation_handler_class, NavigationHandler):
            raise AttributeError("navigation_handler_class must be a NavigationHandler!")

        if not self.scheduler.running:
            self.scheduler.start()
        if polling:
            self.updater.start_polling()
        if idle:
            self.updater.idle()

    def _send_start_message(
            self,
            update: Update,
            _: CallbackContext
    ) -> None:
        """
        Start bot telegram session.
        """
        chat = update.effective_chat

        if chat is None:
            raise AttributeError("Error! Chat object not exist.")
        if self.navigation_handler_class is None:
            raise AttributeError("Error! Navigation handler class not defined.")

        session = self.navigation_handler_class(self._tg_key, chat, self.scheduler)
        self.sessions.append(session)

        if self.start_message_class is None:
            raise AttributeError("Error! Message class not defined.")
        if self.start_message_args is not None:
            start_message = self.start_message_class(session,
                                                     message_args=self.start_message_args)
        else:
            start_message = self.start_message_class(session)

        session.goto_menu(start_message)

    def get_session(
            self,
            chat_id: int = 0
    ) -> Optional["NavigationHandler"]:
        sessions = [x for x in self.sessions if chat_id in (x.chart_id, 0)]
        if not sessions:
            return None
        return sessions[0]

    def _web_app_callback(
            self,
            update: Update,
            context: Any
    ) -> None:
        """
        Callback for webapp results
        """
        if update.effective_chat is None or update.effective_message is None:
            raise AttributeError("Error! Chat or Message object nut found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._send_start_message(update, context)
            return

        session.app_message_webapp_callback(
            update.effective_message.web_app_data.data,
            update.effective_message.web_app_data.button_text
        )

    def _button_select_callback(
            self,
            update: Update,
            context: CallbackContext
    ) -> None:
        """
        Select callback for menu item
        """
        if update.effective_chat is None:
            raise AttributeError("Error! Chat object nut found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._send_start_message(update, context)
            return

        session.select_menu_button(update.message.text)

    def _poll_answer(
            self,
            update: Update,
            _: CallbackContext
    ) -> None:
        """
        Used for poll session.
        """
        if update.effective_user is None:
            raise AttributeError("Error! user object not found.")

        session = next((x for x in self.sessions if x.user_name == update.effective_user.first_name), None)

        if session:
            session.poll_aswer(update.poll_answer.option_ids[0])

    def _button_inline_select_callback(
            self,
            update: Update,
            context: CallbackContext
    ) -> None:
        """
        Select inline callback.
        """
        if update.effective_chat is None:
            raise AttributeError("Error! Chat object nut found.")

        session = self.get_session(update.effective_chat.id)

        if session is None:
            self._send_start_message(update, context)
            return

        session.app_message_button_callback(
            update.callback_query.data,
            update.callback_query.id
        )
