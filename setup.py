# coding: utf-8
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()


# FIXME
def _python2_compat():
    import sys
    if sys.version_info < (3,):
        yield 'configparser'
        yield 'pathlib'


setup(
    name='django-develop',
    description='Django development for humans',
    url='https://github.com/pjdelport/django-develop',

    package_dir={'': 'src'},
    packages=find_packages('src'),

    author=u'Piët Delport',
    author_email='pjdelport@gmail.com',

    setup_requires=['setuptools_scm'],
    use_scm_version=True,

    install_requires=[
        # attrs 15.2.0 (2015-12-08) adds the convert feature.
        'attrs >=15.2.0',
        'Django',
    ] + list(_python2_compat()),

    # The django-develop command-line script
    entry_points={
        'console_scripts': [
            'django-develop = django_develop.cli:main',
            'django-develop-config = django_develop.cli:main_config',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities',
    ],
)
