import logging
import click
# from .version import __version__

from python_telegram_menu import __version__


logging.basicConfig()
log = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version=__version__)
def main():
    print("Hellow from my menu package!")


if __name__ == "__main__":
    main()
