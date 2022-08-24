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
    from python

    -telegram - menu
    import NavigationHandler

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


class AbstractMessage(ABC):
    """
    Abstract message class

    Parameters:
    - navigation: navigation manager
    - label: message label
    - expiry_period: duration before message is deleted
    - inlined: create an inlined message instead of a menu message
    - home_after: go back to home menu after executing the action
    - notification: show a notification in Telegram interface
    """

    EXPIRING_DELAY = 12
    time_alive: datetime.datetime

    def __init__(
            self,
            navigation: "NavigationHandler",
            label: str = "",
            expiry_period: Optional[datetime.timedelta] = None,
            home_after: bool = False,
            inlined: bool = False,
            notification: bool = True,
            input_field: str = "",
            **args: Any,
    ) -> None
        self.keyboard: TypeKeyboard = {{}}
        self.label = emoji_replace(label)
        self.inlined = inlined
        self.notification = notification
        self.navigation = navigation
        self.input_field = input_field
        self.keyboard_previous: TypeKeyboard = [[]]
        self.content_previouse: str = ""
        self.home_after = home_after
        self.message_id = -1
        self.expiry_period = (
            expiry_period
            if isinstance(expiry_period, datetime.timedelta)
            else datetime.timedelta(minutes=self.EXPIRING_DELAY)
        )
        self._status = None
