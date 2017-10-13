import io
import os.path
import string
import sys
from textwrap import dedent

from hypothesis import given, example, note, assume
from hypothesis.strategies import text

from py2_compat import unittest, mock

from django_develop import utils


TEST_ROOT = os.path.dirname(__file__)


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
        with mock.patch('sys.path', [TEST_ROOT]):
            self.assertEqual(
                list(utils.discover_candidate_settings()),
                [(TEST_ROOT, [
                    'test_examples.error_settings',
                    'test_examples.likely_settings',
                    'test_examples.no_likely_settings',
                    'test_examples.no_settings',
                ])])


class TestFindPotentialProblems(unittest.TestCase):
    """
    `utils.find_potential_problems()`
    """

    def test_import_failures(self):
        """
        Flag import failures.
        """
        # Python 3.6 introduced ModuleNotFoundError.
        # https://docs.python.org/3/whatsnew/3.6.html#other-language-changes
        _ModuleNotFoundError = 'ImportError' if sys.version_info < (3, 6) else 'ModuleNotFoundError'

        cases = {
            '': {'import raised ValueError'},
            '.': {'import raised TypeError'},
            '..': {'import raised TypeError'},
            '.foo': {'import raised TypeError'},
            ' ': {'import raised {}'.format(_ModuleNotFoundError)},
            'nonexistent': {'import raised {}'.format(_ModuleNotFoundError)},
            'not.existent': {'import raised {}'.format(_ModuleNotFoundError)},
            'test_examples.error_settings': {'import raised NameError'},
        }
        for (modname, problems) in cases.items():
            with self.subTest(modname=modname):
                self.assertEqual(utils.find_potential_problems(modname), problems)

    def test_problems(self):
        """
        Flag importable modules with with problems.
        """
        cases = {
            'test_examples.no_settings': {'no uppercase names'},
            'test_examples.no_likely_settings': {'no likely setting names'},
        }
        for (modname, problems) in cases.items():
            with self.subTest(modname=modname):
                self.assertEqual(utils.find_potential_problems(modname), problems)

    def test_likely_settings(self):
        """
        Pass modules with likely setting names.
        """
        self.assertEqual(
            utils.find_potential_problems('test_examples.likely_settings'),
            set())

    def test_individual_likely_settings(self):
        """
        The presence of any one of these settings makes a module count as likely.
        """
        likely_names = [
            'DATABASES',
            'EMAIL_BACKEND',
            'INSTALLED_APPS',
            'MEDIA_ROOT',
            'MEDIA_URL',
            'MIDDLEWARE_CLASSES',
            'ROOT_URLCONF',
            'SECRET_KEY',
            'SITE_ID',
            'STATIC_ROOT',
            'STATIC_URL',
        ]
        for name in likely_names:
            with self.subTest(name=name):
                with mock.patch.multiple('test_examples.no_likely_settings', create=True,
                                         **{name: 'dummy'}):
                        self.assertEqual(
                            utils.find_potential_problems('test_examples.no_likely_settings'),
                            set())


class TestPrintCandidateSettings(unittest.TestCase):
    """
    `utils.print_candidate_settings()`
    """

    def _patch_stdout(self):
        # Python 2 compatibility: Intercept sys.stdout with BytesIO instead of StringIO.
        return mock.patch('sys.stdout', new_callable=(
            io.BytesIO if sys.version_info < (3,) else io.StringIO))

    def test_no_candidates(self):
        """
        Printing out no candidates.
        """
        with mock.patch('sys.path', []):
            with self._patch_stdout() as stdout:
                utils.print_candidate_settings()

        self.assertEqual(stdout.getvalue(), dedent("""\
            Looking for usable Django settings modules in Python path... None found.

            """))

    def test_likely_candidates(self):
        """
        Printing a likely candidate.
        """
        with self._patch_stdout() as stdout:
            utils.print_candidate_settings()

        self.assertEqual(stdout.getvalue(), dedent("""\
            Looking for usable Django settings modules in Python path... Found:

                In {}:

                    test_examples.likely_settings

            """.format(TEST_ROOT)))

    def test_all_candidates(self):
        """
        Printing and reporting problematic candidates too.
        """
        with mock.patch('sys.path', [TEST_ROOT]):
            with self._patch_stdout() as stdout:
                utils.print_candidate_settings(include_problems=True)

        self.assertEqual(stdout.getvalue(), dedent("""\
            Looking for usable Django settings modules in Python path... Found:

                In {}:

                    test_examples.error_settings (import raised NameError)
                    test_examples.likely_settings
                    test_examples.no_likely_settings (no likely setting names)
                    test_examples.no_settings (no uppercase names)

            """.format(TEST_ROOT)))
