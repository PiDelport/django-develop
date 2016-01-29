from __future__ import print_function

import sys
import pkgutil


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


def is_candidate_settings(name):
    # TODO: Smarter heuristic: Check for known Django setting name definitions.
    return 'settings' in name and name not in _ignored_settings_modules


def find_candidate_settings():

    def report_candidate(name):
        if is_candidate_settings(name):
            print('Warning: import failed for {}'.format(name))

    # XXX: Copy sys.path with list(), to avoid weird effects from mutation while we iterate.
    for sys_path_entry in list(sys.path):
        candidates = [
            name
            for (loader, name, is_pkg) in pkgutil.walk_packages([sys_path_entry],
                                                                onerror=report_candidate)
            if not is_pkg and is_candidate_settings(name)
            ]
        if 0 < len(candidates):
            yield (sys_path_entry, candidates)


def print_candidate_settings():
    # TODO (Python 3): Use print(..., flush=True) instead
    print('Discovering usable Django settings modules...', end=' ')
    sys.stdout.flush()

    candidate_groups = list(find_candidate_settings())
    if 0 < len(candidate_groups):
        print('Found:')
        print()
        for (sys_path_entry, candidates) in candidate_groups:
            print('    In {}:'.format(sys_path_entry))
            print()
            for candidate in candidates:
                print('        {}'.format(candidate))
            print()
    else:
        print('None found.')
