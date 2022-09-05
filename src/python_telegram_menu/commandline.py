import logging
import click
import .vertion


from importlib import reload
reload(.vertion)

#from .version import __version__


logging.basicConfig()
log = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version=.version.__version__)
def main():
    print("Hellow from my menu package!")


if __name__ == "__main__":
    main()
