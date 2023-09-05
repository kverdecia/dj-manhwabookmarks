#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from djmanhwabookmarks/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


version = get_version("djmanhwabookmarks", "__init__.py")


if sys.argv[-1] == "publish":
    try:
        import wheel

        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()

if sys.argv[-1] == "tag":
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open("README.rst").read()
history = open("HISTORY.rst").read().replace(".. :changelog:", "")

setup(
    extras_require={
        "dev": [
            "invoke",
            "twine",
            "zest.releaser",
            "coverage==4.4.1",
            "mock>=1.0.1",
            "flake8>=2.1.0",
            "tox>=1.7.0",
            "codecov>=2.0.0",
            "mypy",
            "django-stubs[compatible-mypy]",
            "django-stubs-ext",
            "black",
            "vistir==0.6.1",
            "pipenv-setup[black]",
            "pre-commit",
        ]
    },
    name="dj-manhwabookmarks",
    version=version,
    description="""Bookmarks on manhwas""",
    long_description=readme + "\n\n" + history,
    author="Karel Antonio Verdecia Ortiz",
    author_email="kverdecia@gmail.com",
    url="https://github.com/kverdecia/dj-manhwabookmarks",
    packages=[
        "djmanhwabookmarks",
    ],
    python_requires=">=3.11",
    include_package_data=True,
    install_requires=["django>=4.2", "mechanicalsoup", "django-htmx"],
    license="MIT",
    zip_safe=False,
    keywords="dj-manhwabookmarks",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django :: 2.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.11",
    ],
)
