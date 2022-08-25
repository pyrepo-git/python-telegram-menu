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

# if TYPE_CHECKING:
#   from python_telegram_menu import NavigationHandler

logger = logging.getLogger(__name__)

TypeCallback = Optional[Union[Callable[..., Any]]], "BaseMessage"
TypeKeyboard = List[List["ButtonData"]]


class ButtonActions(Enum):
    """
    Button actions.
    """
    HOME = auto(int)
    BACK = auto(int)


class ButtonTypes(Enum):
    """
    Button types
    """
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
    ) -> None:
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
    ) -> None:
        self.keyboard: TypeKeyboard = [[]]
        self.label = emoji_replace(label)
        self.inlined = inlined
        self.notification = notification
        self.navigation = navigation
        self.input_field = input_field
        self.keyboard_previous: TypeKeyboard = [[]]
        self.content_previous: str = ""
        self.home_after = home_after
        self.message_id = -1
        self.expiry_period = (
            expiry_period
            if isinstance(expiry_period, datetime.timedelta)
            else datetime.timedelta(minutes=self.EXPIRING_DELAY)
        )
        self._status = None

    @abstractmethod
    def update(self) -> str:
        """
        Update message content.

        Returns:
        - Message content formatted with HTML formatting/
        """
        raise NotImplementedError

    def text_input(self, text: str) -> None:
        """
        Receive text from console.

        If used, this function must be instantiated in the child class.

        Parameters:
        - text: text received from console
        """

    def get_button(self, label: str) -> Optional[ButtonDef]:
        """
        Get button matching given label/

        Parameters:
        - label: matching label

        Returns:
        - button matching by label

        Returns:
        - EnvironmentError : too many buttons matching label
        """
        return next(iter(y for x in self.keyboard for y in x if y.label == label), None)

    def add_button_back(self, **kwargs: Any) -> None:
        """
        Add a button to go back to previous menu.

        Parameters:
        - label: button label
        - callback: method called on button selection
        """
        self.add_button(label="Back", callback=None, **kwargs)

    def add_button_home(self, **kwargs) -> None:
        """
        Add a button to go back to main menu.

        - label: button label
        - callback: method called on button selection
        """
        self.add_button(label="Home", collback=None, **kwargs)
