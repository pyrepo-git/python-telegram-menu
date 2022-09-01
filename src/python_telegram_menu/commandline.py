import logging
import click

from _version import __version__

logging.basicConfig()
log = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version=__version__)
def main():
    print("Hellow my menu package")


if __name__ == "__main__":
    main()
