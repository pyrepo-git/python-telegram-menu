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
from .core import AbstractMessage, Button, ButtonTypes
from .navigation import NavigationHandler

logger = logging.getLogger(__name__)


class Session:
    """
    Telegram session.
    Send start message to each new user connecting to the bot.
    """
    TIMEOUT_READ = 5
    TIMEOUT_CONNECT = TIMEOUT_READ
    INIT_MESSAGE = "start"

    def __init(
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
            raise KeyError("Telegram API Key must be a string")

        self.updater = telegram.ext.Updater(
            tg_key,
            use_context=True,
            request_kwargs={"read_timeout": self.TIMEOUT_READ,
                            "connection_timeout" : self.TIMEOUT_CONNECT}
        )

        bot: Bot = self.updater.bot
        dispatcher: Dispatcher = self.updater.dispatcher
        self.scheduler = self.updater.job_queue.scheduler

        try:
            logger.info(f"Connected to Telegram bot {bot.name}({bot.first_name})")
        except Unauthorized as error:
            raise AttributeError(f"Bot matching by key {tg_key} not found") from error

        self.tg_key = tg_key
        self.sessions: List[NavigationHandler] =[]
        self.start_message_class: Optional[Type[AbstractMessage]] = None
        self.start_message_args: Optional[List[Any]] = None
        self.navigation_handler_class: Optional[Type["NavigationHandler"]] = None

        # add command handlers
        dispatcher.add_handler(CommandHandler(init_message, self._send_start_message_))
        dispatcher.add_handler(MessageHandler(telegram.ext.Filters.text, self._button_select_callback))
