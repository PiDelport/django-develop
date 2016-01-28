from py2_compat import unittest, mock

from django_develop import utils


class TestVirtualEnvDetection(unittest.TestCase):

    def test_is_inside_virtual_env(self):
        """
        Check `utils.is_inside_virtual_env()` against various sets of sys prefix paths.
        """
        system = mock.sentinel.system
        virtual = mock.sentinel.virtual

        # These are the sets of sys module attributes that should be present or absent
        # with various versions of Python and virtualenv / venv.
        test_cases = {
            'py2_base': dict(prefix=system),
            # Python 3 (as of 3.3 / PEP 405) adds a sys.base_prefix attribute
            'py3_base': dict(base_prefix=system, prefix=system),
            'py3_venv': dict(base_prefix=system, prefix=virtual),
            # virtualenv saves sys.real_prefix, and changes the others
            'py2_virtualenv': dict(real_prefix=system, prefix=virtual),
            'py3_virtualenv': dict(real_prefix=system, prefix=virtual, base_prefix=virtual),
        }

        for (label, sys_attrs) in test_cases.items():
            with self.subTest(label=label):
                # Note: The spec=[] is important so that absent sys_attrs raise AttributeError
                # instead of returning mocks.
                with mock.patch('django_develop.utils.sys', spec=[], **sys_attrs):
                    expected = sys_attrs['prefix'] is virtual
                    self.assertEqual(utils.is_inside_virtual_env(), expected)
