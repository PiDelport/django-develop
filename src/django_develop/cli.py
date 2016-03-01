from __future__ import print_function, unicode_literals

import importlib
import os
import sys
from pathlib import Path

from attr import attributes, attr
from django.conf import settings, ENVIRONMENT_VARIABLE
from django.core.management import ManagementUtility, color_style

from configparser import RawConfigParser

from django_develop import utils


@attributes
class DjangoDevelop(object):

    instance_path = attr(convert=Path)  # type: Path

    @property
    def _config_path(self):
        return self.instance_path / 'django-develop.ini'

    def read_config(self):
        config = RawConfigParser()
        config.read([str(self._config_path)])
        return config

    def write_config(self, config):
        # XXX: Python 2's ConfigParser seems to need a non-Unicode output file?
        mode = 'w' if (3,) <= sys.version_info else 'wb'
        with self._config_path.open(mode) as f:
            config.write(f)

    def init_instance(self, base_settings_module):
        """
        Create the Django instance directory and save django-develop's config file.
        """
        if not self.instance_path.exists():
            print('Creating {}'.format(self.instance_path))
            self.instance_path.mkdir(parents=True)

        config = self.read_config()

        if not config.has_section('django-develop'):
            config.add_section('django-develop')
        config.set('django-develop', 'base_settings_module', base_settings_module)

        self.write_config(config)

    def activate_dev_settings(self):
        """
        Prepare `django_develop.dev_settings`, and point DJANGO_SETTINGS_MODULE at it.
        """
        assert not settings.configured, 'Django settings already configured!'

        from django_develop import dev_settings

        # Import the base settings module
        config = self.read_config()
        base_settings_module = config.get('django-develop', 'base_settings_module')
        try:
            base_mod = importlib.import_module(base_settings_module)
        except ImportError:
            print('Failed to import Django settings module {!r}. Try django-develop-config?'
                  .format(base_settings_module),
                  file=sys.stderr)
            print('', file=sys.stderr)
            # Re-raise the error so that the user can see and diagnose the traceback.
            raise

        for name in dir(base_mod):
            if name.isupper():
                value = getattr(base_mod, name)
                setattr(dev_settings, name, value)

        # Special-case handling: If any of these core settings are explicitly
        # set to an empty value in the base settings module, unset them here
        # so that the defaults below will take their place.
        #
        # This prevents configuration errors due to settings modules that do
        # "from django.conf.global_settings import *"
        # (even though they shouldn't)
        #
        empty_specials_in_global_settings = [
            'SECRET_KEY',
            'DATABASES',
            'STATIC_ROOT',
            'MEDIA_ROOT',
        ]
        for name in empty_specials_in_global_settings:
            if hasattr(dev_settings, name) and not getattr(dev_settings, name):
                delattr(dev_settings, name)

        # Similar to the above, if all the email settings are explicitly set
        # and equal to Django's global default values, then clear them.
        #
        email_defaults_in_global_settings = {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': 'localhost',
            'EMAIL_PORT': 25,
            'EMAIL_HOST_USER': '',
            'EMAIL_HOST_PASSWORD': '',
            'EMAIL_USE_TLS': False,
            'EMAIL_USE_SSL': False,
            'EMAIL_SSL_CERTFILE': None,
            'EMAIL_SSL_KEYFILE': None,
            'EMAIL_TIMEOUT': None,
        }
        if all(hasattr(dev_settings, name) and getattr(dev_settings, name) == value
               for (name, value) in email_defaults_in_global_settings.items()):
            for name in email_defaults_in_global_settings.keys():
                delattr(dev_settings, name)

        # Add django-development defaults
        defaults = {
            # The usual required settings
            'SECRET_KEY': 'development key for {}'.format(self.instance_path),
            'ROOT_URLCONF': 'django_develop.dev_urls',
            'DATABASES': {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': str(self.instance_path / 'db.sqlite3'),
                    'ATOMIC_REQUESTS': True,
                },
            },
            # Generally useful for development
            'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
            'STATIC_ROOT': str(self.instance_path / 'static_files'),
            'MEDIA_ROOT': str(self.instance_path / 'media_files'),
        }
        for (name, value) in defaults.items():
            if not hasattr(dev_settings, name):
                setattr(dev_settings, name, value)

        # For now, always enable DEBUG.
        # This overrides any "DEBUG = False" that the base settings module may have imported.
        # TODO: Provide a convenient way to toggle this? (Would that really be useful?)
        dev_settings.DEBUG = True

        # Set DJANGO_SETTINGS_MODULE
        if (ENVIRONMENT_VARIABLE in os.environ and
                os.environ[ENVIRONMENT_VARIABLE] != 'django_develop.dev_settings'):
            print('django-develop warning: disregarding existing {} ({!r})'.format(
                ENVIRONMENT_VARIABLE, os.environ[ENVIRONMENT_VARIABLE]))

        os.environ[ENVIRONMENT_VARIABLE] = 'django_develop.dev_settings'


def _fail(*lines):
    """
    :raises: SystemExit
    """
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(2)


def _get_DjangoDevelop():
    virtualenv_path = Path(sys.prefix)
    return DjangoDevelop(virtualenv_path / 'django-develop-instance')


def main():
    """
    django-develop CLI entry point.
    """
    # XXX: Bail out early if being invoked for autocompletion.
    utility = ManagementUtility()
    utility.autocomplete()

    if not utils.is_inside_virtual_env():
        _fail('Run django-develop inside a virtualenv')

    dd = _get_DjangoDevelop()

    if not dd.instance_path.exists():
        _fail('django-develop not configured, try "django-develop-config"')
    else:
        # Set up and hand over to Django
        dd.activate_dev_settings()

        utility.execute()


def main_config():
    """
    django-develop-config CLI entry point.
    """
    style = color_style()

    if not utils.is_inside_virtual_env():
        _fail('Run django-develop-config inside a virtualenv')

    dd = _get_DjangoDevelop()  # type: DjangoDevelop
    try:
        [base_settings_module] = sys.argv[1:2]
    except ValueError:
        print('Usage: django-develop-config <base_settings_module>')
        print()

        # Show current configuration
        if dd.instance_path.exists():
            print('Instance directory: {}'.format(dd.instance_path))
            print()
        config = dd.read_config()
        base_settings_module = config.get('django-develop', 'base_settings_module', fallback=None)
        print('Current base settings module: {}'.format(
            style.SUCCESS(base_settings_module) if base_settings_module else
            'not configured'))
        print()

        # TODO: Add CLI flag for include_problems?
        utils.print_candidate_settings()

        raise SystemExit(2)
    else:
        dd.init_instance(base_settings_module)
