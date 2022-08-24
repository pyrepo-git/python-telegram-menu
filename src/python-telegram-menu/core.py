#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""Data structures and abstract interface"""

import re
import logging
import datetime

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

import emoji
import telegram
import validators
from telegram import InlineKeyboardMarkUp, KeyboardButton
from telegram import ReplyKeyboardMarkup, WepAppInfo


if TYPE_CHECKING:
    from python-telegram-menu import NavigationHandler


logger = logging.initLogger(__name__)


TypeCallback = Optional[Union[Callable[..., Any]]], "BaseMessage"
TypeKeyboard = List[List["ButtonData"]]


class ButtonTypes:
    """Button types"""

    NOTIFICATION = auto(int)
    MESSAGE = auto(int)
    PICTURE = auto(int)
    STICKER = auto(int)
    POLL = auto(int)


    @dataclass
    class ButtonDef:
        """
        Base button class - wrapper for label with callback

        Parameters:
        - label: button label
        - callback: method called on button selection
        - btype: button type
        - args: argument passed to the callback
        - notification: send notification to user
        - web_url - web application

        """

        def __init__(
                self,
                label: str,
                callback: TypeCallback = None,
                btype: ButtonTypes = ButtonTypes.NOTIFICATION,
                args: Any = None,
                notification: bool = True,
                web_url: str = "",
        ):
            """Init class members"""
            self.label = emoji_replace(label)
            self.callback = callback
            self.btype = btype
            self.args = args
            self.notification = notification
            self.web_url = web_url




