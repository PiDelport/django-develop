from io import StringIO

from py2_compat import unittest, mock

from django_develop import cli


def _patch_inside_virtual_env(expected):
    return mock.patch('django_develop.utils.is_inside_virtual_env',
                      mock.Mock(return_value=expected))


@mock.patch('sys.stderr', new_callable=StringIO)
class TestMain(unittest.TestCase):
    """
    Test `cli.main()`.
    """

    def test_outside_virtualenv(self, stderr):
        with _patch_inside_virtual_env(False):
            with self.assertRaises(SystemExit) as raised:
                cli.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(stderr.getvalue().splitlines(),
                         ['Run django-develop inside a virtualenv'])

    def test_inside_virtualenv(self, stderr):
        with _patch_inside_virtual_env(True):
            with self.assertRaises(SystemExit) as raised:
                cli.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(stderr.getvalue().splitlines(),
                         ['django-develop not configured, try "django-develop init"'])
