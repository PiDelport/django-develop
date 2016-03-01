import os.path
import string

from hypothesis import given, example, note, assume
from hypothesis.strategies import text

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


class TestIsCandidateName(unittest.TestCase):
    """
    `utils.is_candidate_name()`
    """

    # Hacky strategy for module names
    modnames = text(string.printable).map(str)

    @given(modnames.filter(lambda s: 'settings' not in s))
    @example('not_a_setting')
    def test_non_candidates(self, modname):
        """
        Random names aren't candidates.
        """
        self.assertFalse(utils.is_candidate_name(modname))

    @given(modnames, modnames)
    @example('foo_', '_bar')
    @example('app.', '.mod')
    def test_candidates(self, pre, post):
        """
        Names containing "settings" are candidates.
        """
        modname = pre + 'settings' + post
        note('modname={!r}'.format(modname))
        self.assertTrue(utils.is_candidate_name(modname))

    # Special-cased names
    specials = [
        'django.conf.global_settings',
        'django.core.management.commands.diffsettings',
        'django_develop.dev_settings',
    ]

    def test_exceptions(self):
        """
        The special-cased names are not candidates.
        """
        for modname in self.specials:
            with self.subTest(modname=modname):
                self.assertFalse(utils.is_candidate_name(modname))

    @given(modnames, modnames)
    @example('foo_', '_bar')
    @example('app.', '.mod')
    def test_modified_exceptions(self, pre, post):
        """
        Prefixed and suffixed versions of the special-cased names are not excepted.
        """
        assume(pre or post)  # Require at least some prefix or suffix
        for special in self.specials:
            modname = pre + special + post
            note('modname={!r}'.format(modname))
            self.assertTrue(utils.is_candidate_name(modname))


class TestDiscoverCandidateSettings(unittest.TestCase):
    """
    `utils.discover_candidate_settings()`
    """

    def test_dummy_path(self):
        """
        Discover no candidates from an empty / dummy `sys.path`.
        """
        paths = [
            [],
            ['dummy'],
            ['foo', 'bar'],
        ]
        for path in paths:
            with self.subTest(path=path):
                with mock.patch('sys.path', path):
                    self.assertEqual(
                        list(utils.discover_candidate_settings()),
                        [])

    def test_examples(self):
        """
        Discover the example settings modules.
        """
        # Limit the search to the test root to avoid having to mask out third-party modules,
        # such as hypothesis._settings.
        test_root = os.path.dirname(__file__)
        with mock.patch('sys.path', [test_root]):
            self.assertEqual(
                list(utils.discover_candidate_settings()),
                [(test_root, [
                    'test_examples.error_settings',
                    'test_examples.likely_settings',
                    'test_examples.no_likely_settings',
                    'test_examples.no_settings',
                ])])
