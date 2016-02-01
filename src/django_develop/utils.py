from __future__ import print_function

import sys
import pkgutil
import importlib

from django.core.management.color import color_style


def is_inside_virtual_env():
    """
    Detect whether a Python virtual environment is active.

    This detects environments created using virtualenv, or using Python's built-in venv (PEP 405).
    If true, `sys.prefix` should be the virtual environment's root.

    This implementation only looks at the `sys` module,
    so environment variables like VIRTUAL_ENV do not affect it.

    :rtype: bool
    """
    is_virtualenv = hasattr(sys, 'real_prefix')
    is_venv = hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix
    return is_virtualenv or is_venv


_ignored_settings_modules = {
    'django.conf.global_settings',
    'django.core.management.commands.diffsettings',
    'django_develop.dev_settings',
}


def is_candidate_name(modname):
    """
    Quick check for candidate Django settings module names.
    """
    return 'settings' in modname and modname not in _ignored_settings_modules


def discover_candidate_settings():
    """
    Discover candidate settings modules by name.

    This does not import or inspect the contents of the modules.

    :return: List of (sys.path entry, [module names])
    """

    def report_candidate(modname):
        if is_candidate_name(modname):
            print('Warning: import failed for {}'.format(modname))

    # XXX: Copy sys.path with list(), to avoid weird effects from mutation while we iterate.
    for sys_path_entry in list(sys.path):
        modnames = [
            modname
            for (finder, modname, is_pkg) in pkgutil.walk_packages([sys_path_entry],
                                                                   onerror=report_candidate)
            if not is_pkg and is_candidate_name(modname)
        ]
        if 0 < len(modnames):
            yield (sys_path_entry, modnames)

# The presence of any of these settings indicate a likely Django settings module.
_likely_setting_names = {
    # XXX: Too common?
    # 'DEBUG',

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
}


def find_potential_problems(modname):
    """
    Heuristically check if `modname` is a likely settings module.

    Returns a set of short problem descriptions, which will be empty for likely settings modules.

    :rtype: set
    """
    def problems():
        try:
            mod = importlib.import_module(modname)
        except Exception as e:
            yield 'import raised {}'.format(type(e).__name__)
            return

        names = set(dir(mod))
        if not any(name.isupper() for name in names):
            yield 'no uppercase names'
        elif not _likely_setting_names & names:
            yield 'no likely setting names'

    return set(problems())


def print_candidate_settings(include_problems=False):
    """
    Discover and print candidate usable Django settings modules to standard output.

    :param include_problems:
        If true, include candidate modules with problems.
        This should mainly be useful for troubleshooting.
    """
    style = color_style()

    # TODO (Python 3): Use print(..., flush=True) instead
    print('Looking for usable Django settings modules in Python path...', end=' ')
    sys.stdout.flush()

    candidate_groups = list(discover_candidate_settings())
    if 0 < len(candidate_groups):
        print('Found:')
        print()
        for (sys_path_entry, modnames) in candidate_groups:
            # XXX: A bit messy.
            if not include_problems:
                modnames = [n for n in modnames if not find_potential_problems(n)]

            if 0 < len(modnames):
                print('    In {}:'.format(sys_path_entry))
                print()
                for modname in modnames:
                    problems = find_potential_problems(modname)
                    if not problems:
                        print('        {}'.format(style.SUCCESS(modname)))
                    elif include_problems:
                        print('        {} ({})'.format(modname, ', '.join(problems)))
                print()
    else:
        print('None found.')
