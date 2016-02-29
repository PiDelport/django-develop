==============
django-develop
==============

Django development for humans.

.. image:: https://img.shields.io/pypi/v/django-develop.svg
    :target: https://pypi.python.org/pypi/django-develop

.. image:: https://img.shields.io/badge/source-GitHub-lightgrey.svg
    :target: https://github.com/pjdelport/django-develop

.. image:: https://img.shields.io/github/issues/pjdelport/django-develop.svg
    :target: https://github.com/pjdelport/django-develop/issues?q=is:open

.. image:: https://travis-ci.org/pjdelport/django-develop.svg?branch=master
    :target: https://travis-ci.org/pjdelport/django-develop

.. image:: https://codecov.io/github/pjdelport/django-develop/coverage.svg?branch=master
    :target: https://codecov.io/github/pjdelport/django-develop?branch=master


Quick Start
===========

1. Create a virtual environment with your Django project installed::

    $ mkvirtualenv my-app
    $ pip install -e .

2. Install ``django-develop``::

    $ pip install django-develop

2. Select your project's base settings module::

    $ django-develop-config
    …
    $ django-develop-config my_app.base_settings

3. Use ``django-develop`` as you would normally use ``django-admin``::

    $ django-develop check
    $ django-develop migrate
    $ django-develop runserver


Contributing
============

See `<HACKING.rst>`__.
