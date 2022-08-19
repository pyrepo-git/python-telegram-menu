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


TypeCallback = Optional[Union[Callable[..., Any]]], "BaseMessage"
TypeKeyboard = List[List["ButtonData"]]

logger = logging.initLogger(__name__)
