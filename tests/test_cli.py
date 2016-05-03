from io import StringIO
from pathlib import Path

from py2_compat import unittest, mock, TemporaryDirectory

from django_develop import cli


def _patch_inside_virtual_env(expected):
    return mock.patch('django_develop.utils.is_inside_virtual_env',
                      mock.Mock(return_value=expected))


class TestDjangoDevelop(unittest.TestCase):

    def setUp(self):
        # Get a temporary instance directory
        temp_dir = TemporaryDirectory()
        self.instance_dir = temp_dir.name
        self.addCleanup(temp_dir.cleanup)

        self.dd = cli.DjangoDevelop(self.instance_dir)

    def test_read_write_config(self):
        config_path = Path(self.instance_dir, 'django-develop.ini')

        self.assertFalse(config_path.exists())
        config = self.dd.read_config()
        self.dd.write_config(config)
        self.assertTrue(config_path.is_file())
        self.assertEqual(config_path.stat().st_size, 0)


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
                         ['django-develop not configured, try "django-develop-config"'])
