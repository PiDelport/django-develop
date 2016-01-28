from __future__ import print_function

import importlib
import os
import sys
from pathlib import Path

from attr import attributes, attr
from django.conf import settings, ENVIRONMENT_VARIABLE
from django.core.management import ManagementUtility

from django_develop.compat import RawConfigParser
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
        with self._config_path.open('w') as f:
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
        base_mod = importlib.import_module(base_settings_module)
        for name in dir(base_mod):
            if name.isupper():
                value = getattr(base_mod, name)
                setattr(dev_settings, name, value)

        # Add django-development defaults
        defaults = {
            # The usual required settings
            'DEBUG': True,
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

        # Set DJANGO_SETTINGS_MODULE
        if (ENVIRONMENT_VARIABLE in os.environ and
                os.environ[ENVIRONMENT_VARIABLE] != 'django_develop.dev_settings'):
            print('django-develop warning: disregarding existing {} ({!r})'.format(
                ENVIRONMENT_VARIABLE, os.environ[ENVIRONMENT_VARIABLE]))

        os.environ[ENVIRONMENT_VARIABLE] = 'django_develop.dev_settings'


def main():
    """
    django-develop CLI entry point.
    """
    # XXX: Bail out early if being invoked for autocompletion.
    utility = ManagementUtility()
    utility.autocomplete()

    if not utils.is_inside_virtual_env():
        print('Run django-develop inside a virtualenv')
        raise SystemExit()
    virtualenv_path = Path(sys.prefix)

    dd = DjangoDevelop(virtualenv_path / 'django-develop-instance')

    if sys.argv[1:2] == ['init']:
        # XXX: Special-cased, for now
        try:
            [base_settings_module] = sys.argv[2:3]
        except ValueError:
            print('Usage: django-develop init <base_settings_module>')
            print()
            utils.print_candidate_settings()
            raise SystemExit()
        else:
            dd.init_instance(base_settings_module)
    elif not dd.instance_path.exists():
        print('django-develop not configured, try "django-develop init"')
    else:
        # Set up and hand over to Django
        dd.activate_dev_settings()

        utility.execute()
