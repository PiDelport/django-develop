"""
Backward compatibility imports.
"""
import sys

if sys.version_info < (3, 3):
    import unittest2 as unittest
    import mock
else:
    import unittest
    from unittest import mock
