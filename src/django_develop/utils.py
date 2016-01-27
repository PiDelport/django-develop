from __future__ import print_function

import sys
import pkgutil


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
    for path_entry in list(sys.path):
        candidates = [
            name
            for (loader, name, is_pkg) in pkgutil.walk_packages([path_entry],
                                                                onerror=report_candidate)
            if not is_pkg and is_candidate_settings(name)
            ]
        if 0 < len(candidates):
            yield (path_entry, candidates)


def print_candidate_settings():
    print('Possible settings modules found:')
    print()
    for (path_entry, candidates) in find_candidate_settings():
        print('    From {}:'.format(path_entry))
        print()
        for candidate in candidates:
            print('        {}'.format(candidate))
        print()
