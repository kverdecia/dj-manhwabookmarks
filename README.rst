=============================
dj-manhwabookmarks
=============================

.. image:: https://badge.fury.io/py/dj-manhwabookmarks.svg
    :target: https://badge.fury.io/py/dj-manhwabookmarks

.. image:: https://travis-ci.org/kverdecia/dj-manhwabookmarks.svg?branch=master
    :target: https://travis-ci.org/kverdecia/dj-manhwabookmarks

.. image:: https://codecov.io/gh/kverdecia/dj-manhwabookmarks/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/kverdecia/dj-manhwabookmarks

Bookmarks on manhwas

Documentation
-------------

The full documentation is at https://dj-manhwabookmarks.readthedocs.io.

Quickstart
----------

Install dj-manhwabookmarks::

    pip install dj-manhwabookmarks

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'djmanhwabookmarks.apps.ManhwaBookmarks',
        ...
    )

Add dj-manhwabookmarks's URL patterns:

.. code-block:: python

    from djmanhwabookmarks import urls as djmanhwabookmarks_urls


    urlpatterns = [
        ...
        url(r'^', include(djmanhwabookmarks_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox


Development commands
---------------------

::

    pip install -r requirements_dev.txt
    invoke -l


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
