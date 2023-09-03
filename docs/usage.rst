=====
Usage
=====

To use dj-manhwabookmarks in a project, add it to your `INSTALLED_APPS`:

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
