=========================
Working on django-develop
=========================


Running the tests
=================

Running ``tox``, ``detox``, or ``pytest`` should all work.

With ``unittest``::

    python -m unittest discover tests


Coverage
========

With ``coverage``::

    coverage run --source src -m unittest discover tests
    coverage report
    coverage html


With ``pytest`` and ``pytest-cov``::

    py.test --cov src
    py.test --cov src --cov-report=html

