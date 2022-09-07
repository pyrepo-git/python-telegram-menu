import codecs
import os.path

from setuptools import setup

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

extras_require = {
    "develop": [
        "check-manifest",
        "pytest",
        "pytest-cov>",
        "pytest-console-scripts",
        "bumpversion>=0.6.0",
        "pyflakes",
        "pre-commit",
        "black",
        "flake8",
        "twine",
        "validators",
        "click",
        "emoji",
        "python-telegram-bot",
    ],
}
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    version=get_version("python_telegram_menu/__init__.py"),
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "python_telegram_menu=python_telegram_menu.commandline:python_telegram_menu"
        ]
    },
)
