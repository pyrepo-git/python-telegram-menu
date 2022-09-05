from setuptools import setup

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
        "emoji",
        "python-telegram-bot",
        "validators",
        "click",
    ],
}
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "python_telegram_menu=python_telegram_menu.commandline:python_telegram_menu"
        ]
    },
)
