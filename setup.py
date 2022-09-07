from setuptools import setup


__version__ = "0.0.1"

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
    version=__version__,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "python_telegram_menu=python_telegram_menu.commandline:python_telegram_menu"
        ]
    },
)
