# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from djangocms_translations import __version__


REQUIREMENTS = [
    'django-cms>=3.5',
    'django-appconf>=1.0,<2',
    'django-extended-choices',
    'djangocms-transfer',
    'pygments',
    'yurl',
    'requests',
    'celery>=3.0,<4.0', # Aldryn-celery supports only 3.X
]


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]


setup(
    name='djangocms-translations',
    version=__version__,
    description='Send django CMS content for translation to 3rd party providers.',
    author='Divio AG',
    author_email='info@divio.ch',
    url='https://github.com/divio/djangocms-translations',
    license='BSD',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    classifiers=CLASSIFIERS,
    test_suite='tests.settings.run',
)
