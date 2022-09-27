"""
Dispatcher for telegram messages
"""

import logging
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict

from python_telegram_menu import (
    Session,
    Handler,
    ABCMessage,
    ButtonTypes,
    Button,
)

from handler import TestHandler


KeyboardContent = List[Union[str, List[str]]]
UpdateCallback = Callable[[Any], None]

ROOT_FOLDER = Path(__file__).parent.parent
TEST_URL = "https://github.com/pyrepo-git/python_telegram_menu"


class InlineMessage(ABCMessage):
    """
    Inline buttons messages.
    """

    MARKER = "inline"

    def __init__(
        self,
        navigation: TestHandler,
        update_callback: Optional[List[UpdateCallback]] = None,
    ) -> None:
        """
        Init method for InlinesMessage class.
        """
        super().__init__(navigation, InlineMessage.MARKER, inlined=True)

        self.pause = True
        if isinstance(update_callback, list):
            update_callback.append(self.update_display)

    def update_display(self) -> None:
        """
        Update content for callback
        """
        self._toggle_play_button()
        if self.edit_message():
            self.init_date_time()

    def kill_message(self) -> None:
        """
        Kill message after on callback
        """
        self._toggle_play_button()

    def action_button(self) -> str:
        """
        Execute action and return notification content.
        """
        self._toggle_play_button()
        return "inline button selected."

    def text_button(self) -> str:
        """
        Display text data.
        """
        self._toggle_play_button()
        data: KeyboardContent = [["text1", "value1"], ["text2", "value2"]]
        return format_list(data)

    def sticker_default(self) -> str:
        """
        Return default sticker.
        """
        self._toggle_play_button()
        return f"{TEST_URL}/resources/stats_default.webp"

    def picture_default(self) -> str:
        """
        Return default picture.
        """
        self._toggle_play_button()
        return "invalid picture path"

    def picture_button(self) -> str:
        """
        Return local picture.
        """
        self._toggle_play_button()
        return (
            (ROOT_FOLDER / "resources" / "packages.png").resolve().as_posix()
        )

    def picture_button_remote(self) -> str:
        """
        Return remote picture.
        """
        self._toggle_play_button()
        return f"{TEST_URL}/resources/classes.png"

    def _toggle_play_button(self) -> None:
        """
        Set play/pause mode.
        """
        self.pause = not self.pause

    @staticmethod
    def action_poll(poll_answer: str) -> None:
        """
        Log poll answer.
        """
        logging.info(f"Poll answer is {poll_answer}")

    def update(self) -> str:
        """
        Update message content.
        """
        poll_question = "Select option:"
        poll_choices = [":play_button:Option " + str(x) for x in range(6)]
        toggle_button = ":play_button:" if self.pause else ":pause_button:"
        self.keyboard = [
            Button(
                toggle_button,
                callback=self.sticker_default,
                btype=ButtonTypes.STICKER,
            ),
            Button(
                ":twisted_rightwards_arrows:",
                callback=self.picture_default,
                btype=ButtonTypes.PICTURE,
            ),
            Button(
                ":chart_with_upwards_trend:",
                callback=self.picture_button,
                btype=ButtonTypes.PICTURE,
            ),
            Button(
                ":chart_with_downwards_trend:",
                callback=self.picture_button_remote,
                btype=ButtonTypes.PICTURE,
            ),
        ]
        self.add_button(
            ":door:", callback=self.text_button, btype=ButtonTypes.MESSAGE
        )
        self.add_button(":speaker_medium_volume:", callback=self.action_button)
        self.add_button(
            ":question:",
            self.action_poll,
            btype=ButtonTypes.POLL,
            args=[poll_question, poll_choices],
        )
        return "Status updated."
