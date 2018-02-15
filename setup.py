# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from djangocms_translations import __version__

REQUIREMENTS = [
    'django-appconf>=1.0,<2',
    'django-extended-choices',
    'pygments',
    'yurl',
    'requests',
    'celery>=3.0,<4.0',  # Aldryn-celery supports only 3.X
    # 'djangocms-transfer',  # Private repo
    # 'django-cms',  # Develop branch
    'django>=1.10,<1.11',  # TODO: 'RadioFieldRenderer' was removed in 1.11
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
    description=open('README.rst').read(),
    author='Divio AG',
    author_email='info@divio.ch',
    url='https://github.com/divio/djangocms-translations',
    packages=find_packages(),
    license='LICENSE',
    platforms=['OS Independent'],
    install_requires=REQUIREMENTS,
    classifiers=CLASSIFIERS,
    include_package_data=True,
    zip_safe=False,
    test_suite='tests.settings.run',
)
