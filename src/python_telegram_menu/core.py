#!/usr/bin/env python 3
# -*- coding: utf-8 -*-

"""
Data structures and abstract interface.
"""

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
from telegram import InlineKeyboardMarkup, KeyboardButton
from telegram import ReplyKeyboardMarkup, WebAppInfo

if TYPE_CHECKING:
    from python_telegram_menu import NavigationHandler

logger = logging.getLogger(__name__)

TypeCallback = Optional[Union[Callable[..., Any], "AbstractMessage"]]
TypeKeyboard = List[List["ButtonData"]]


class ButtonActions(Enum):
    """
    Button actions.
    """
    HOME = auto(int)
    BACK = auto(int)


class ButtonTypes(Enum):
    """
    Button types.
    """
    NOTIFICATION = auto(int)
    MESSAGE = auto(int)
    PICTURE = auto(int)
    STICKER = auto(int)
    POLL = auto(int)


@dataclass
class ButtonData:
    """
    Base button class - wrapper for label with callback.

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
            button_type: ButtonTypes = ButtonTypes.NOTIFICATION,
            args: Any = None,
            notification: bool = True,
            web_url: str = "",
    ) -> None:
        """Init class members"""
        self.label = emoji_replace(label)
        self.callback = callback
        self.button_type = button_type
        self.args = args
        self.notification = notification
        self.web_url = web_url


def emoji_replace(label: str) -> str:
    """
    Replace emoji token with utf-16 code.
    """
    match_emoji = re.findall(r"(:\w+:)", label)
    for item in match_emoji:
        emoji_str = emoji.emojize(item, use_aliases=True)
        label = label.replace(item, emoji_str)
    return label


class AbstractMessage(ABC):
    """
    Abstract message class.

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
            - Message content formatted with HTML formatting
        """
        raise NotImplementedError

    def text_input(self, text: str) -> None:
        """
        Receive text from console.

        If used, this function must be instantiated in the child class.

        Parameters:
            - text: text received from console
        """

    def get_button(self, label: str) -> Optional[ButtonData]:
        """
        Get button matching given label/

        Parameters:
            - label: matching label

        Returns:
            - button matching by label

        Raises:
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

        Parameters:
            - label: button label
            - callback: method called on button selection
        """
        self.add_button(label="Home", callback=None, **kwargs)

    def add_button(
            self,
            label: str,
            callback: TypeCallback = None,
            button_type: ButtonTypes = ButtonTypes.NOTIFICATION,
            args: Any = None,
            notification: bool = False,
            new_row: bool = False,
            web_url: str = "",
    ) -> None:
        """
        Add button to keyboard container.

        Parameters:
            - label: button label
            - callback: method called on button selection
            - button_type: button type
            - args: arguments passed for callback
            - notification: send/not send notification
            - new_row: add/not add new row in keyboard container
            - web_url: web url
        """
        buttons_per_row = 2 if not self.inlined else 4
        if not isinstance(self.keyboard, list) or not self.keyboard:
            self.keyboard = [[]]
        if new_row or len(self.keyboard[-1]) == buttons_per_row:
            self.keyboard.append([ButtonData(label, callback, button_type, args, notification, web_url)])
        else:
            self.keyboard[-1].append(ButtonData(label, callback, button_type, args, notification, web_url))

    def edit_message(self) -> bool:
        """
        Requested navigation controller to update current message.
        """
        return self.notification.edit_message(self)

    def gen_keyboard_content(
            self,
            inlined: Optional[bool] = None,
    ) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
        """
        Generate keyboard content.
        """
        if inlined is None:
            inlined = self.inlined
        keyboard_buttons = []
        button_object = telegram.InlineKeyboardButton if inlined else KeyboardButton

        for row in self.keyboard
            if not self.input_field and row:
                self.input_field = row[0].label

            button_array = []

            for btn in row:
                if btn.web_url and validators.url(btn.web_url):
                    button_array.append(
                        button_object(
                            text=btn.label,
                            web_app=WebAppInfo(url=btn.web_url),
                            callback_data=f"{self.label}.{btn.label}"
                        )
                    )
                else:
                    button_array.append(
                        button_object(
                            text=btn.label,
                            callback_data=f"{self.label}.{btn.label}"
                        )
                    )
            keyboard_buttons.append(button_array)

            if inlined:
                return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons, resize_keyboard=False)

            if self.input_field and self.input_field != "<disable>":
                return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True,
                                           input_field_placeholder=self.input_field)

            return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

    def is_alive(self) -> None:
        """
        Update message timestamp.
        """
        self.time_alive = datetime.datetime.now()

    def is_expired(self) -> bool:
        """
        Return:
            - True: if expiry date of message has expired
        """
        if self.time_alive is not None:
            return self.time_alive + self.expiry_period < datetime.datetime.now()
        return False

    def kill_message(self) -> None:
        """
        Display status before message is destroyed.
        """
        logger.debug(f"Remove message '{self.label}'({self.message_id})")
