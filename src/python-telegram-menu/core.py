#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""Data structure and abstract interface"""

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
from telegram import inlineKeyboardMarkUp, KeyboardButton
from telegram import ReplyKeyboardMarkup, WepAppInfo


if TYPE_CHECKING:
    from python-telegram-menu import NavigationYandler


logger = logging.initLogger(__name__)


TypeCallback = Optional[Union[Callable[..., Any]]], "BaseMessage"
TypeKeyboard = List[List["ButtonData"]]


class ButtonTypes(Enum):
    """Button types"""

    NOTIFICATION = auto()
    MESSAGE = auto()
    PICTURE = auto()
    STICKER = auto()
    POLL = auto()


    @dataclass
    class BUttonDef:
        """
        Base button class? wraper for label with callback

        Parameners:
        - lebel: button label
        - callback: method called on button selection
        - btype: button type
        - args: argument passed to the callback
        - notification: send notification to user

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




