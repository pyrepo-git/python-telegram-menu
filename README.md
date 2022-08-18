# Python library template

A template repository for a modern Python library

[![GitHub Actions Status](https://github.com/matthewfeickert/python-library-template/workflows/CI/CD/badge.svg)](https://github.com/matthewfeickert/python-library-template/actions)
[![Code Coverage](https://codecov.io/gh/matthewfeickert/Python-library-template/graph/badge.svg?branch=master)](https://codecov.io/gh/matthewfeickert/Python-library-template?branch=master)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/matthewfeickert/Python-library-template.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/matthewfeickert/Python-library-template/latest/files/)
[![CodeFactor](https://www.codefactor.io/repository/github/matthewfeickert/Python-library-template/badge)](https://www.codefactor.io/repository/github/matthewfeickert/Python-library-template)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![Docs](https://img.shields.io/badge/docs-master-blue.svg)](https://matthewfeickert.github.io/python-library-template)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/matthewfeickert/python-library-template/master)

<!-- Here libname should be replaced with your library's name on PyPI  -->
[![PyPI version](https://badge.fury.io/py/libname.svg)](https://badge.fury.io/py/libname)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/libname.svg)](https://pypi.org/project/libname/)

The template library is [`libname`](https://github.com/matthewfeickert/Python-library-template/search?q=libname&unscoped_q=libname) to make it clear what is needed for replacement

## Setting up the template for your library

1. Edit `setup.py` to reflect all of your library's needs and requirements
2. Edit the paths to badges in the `README` to match your library's locations
   - Change `libame` to your library's name
   - Change `matthewfeickert` to your username or org name on GitHub
   - Change `python-library-template` to your project name on GitHub (probably the same as the library name)
3. Replace the rest of the `README` contents with your information
4. Run `git grep "libname"` to make sure that you have changed all instances of `libame` (it is easy to miss the dotfiles)
5. Setup accounts with [Codecov](https://codecov.io/), [LGTM](https://lgtm.com/), and [CodeFactor](https://www.codefactor.io/)
   - Also add the [Codecov](https://github.com/marketplace/codecov) and [LGTM](https://github.com/marketplace/lgtm) GitHub marketplace apps
6. Generate a Codecov token and add it to your [GitHub repo's secrets](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/contexts-and-expression-syntax-for-github-actions#contexts) with name `CODECOV_TOKEN`

## Controlling the version number with bumpversion

When you want to increment the version number for a new release use [`bumpversion`](https://github.com/peritus/bumpversion) to do it correctly across the whole library.
For example, to increment to a new patch release you would simply run

```
bumpversion patch
```

which given the [`.bumpversion.cfg`](https://github.com/matthewfeickert/Python-library-template/blob/master/.bumpversion.cfg) makes a new commit that increments the release version by one patch release.
