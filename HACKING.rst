=========================
Working on django-develop
=========================


Running the tests
=================

The test suite uses `Hypothesis`_::

    pip install hypothesis

.. _Hypothesis: https://hypothesis.readthedocs.org/

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

