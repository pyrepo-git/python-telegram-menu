from python_telegram_menu import Handler


class TestHandler(Handler):
    """
    Extended Test Handler with 'Back' command
    """

    def back(self) -> int:
        """
        Return to previous menu keyboard
        """
        return self.select_menu_button('Back')
