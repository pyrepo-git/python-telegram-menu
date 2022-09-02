from setuptools import setup

extras_require = {
    "develop": [
        "check-manifest",
        "pytest>=7.1.2",
        "pytest-cov>=3.0.0",
        "pytest-console-scripts>=1.3.1",
        "bumpversion>=0.6.0",
        "pyflakes",
        "pre-commit",
        "black",
        "flake8",
        "twine",
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
