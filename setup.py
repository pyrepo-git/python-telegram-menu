import os.path

from setuptools import setup

def get_version(version_tuple):
    if not isinstance(version_tuple[-1], int):
        return '.'.join(
            map(str, version_tuple[:-1])
        ) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))
    
    init = os.path.join(
        os.path.dirname(__file__), 'src', 'python_telegram_menu',
        '__init__.py'
    )
    
version_line = list(
    filter(lambda l: l.startswith('VERSION'), open(init))
)[0]

PKG_VERSION = get_version(eval(version_line.split('=')[-1]))
    
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
    version=PKG_VERSION,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "python_telegram_menu=python_telegram_menu.commandline:python_telegram_menu"
        ]
    },
)
