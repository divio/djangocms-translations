django CMS Translations
=======================

Django CMS plugin for translations.


Installation
============

Divio Cloud Users
-----------------

Choose a site you want to install the add-on to from the dashboard. Then go
to ``Apps -> Install app`` and click ``Install`` next to ``django CMS Translations`` app.

Redeploy the site.

Manual Installation
-------------------

::

    git clone git@github.com:divio/djangocms-translations.git
    cd djangocms-translations
    python setup.py develop
    pip install -r tests/requirements.txt
    pip install django-cms  # See supported versions on tox.ini


Please note you need a postgres database running for this to work.

Add ``djangocms_translations`` to ``INSTALLED_APPS``.

Developing via DjangoCMS-helper
-------------------

::

    # Add a POSTGRES database. Consider using user=password=database_name=djangocmstranslations as this is the default for tests/settings.py. Otherwise you'll need to set DJANGOCMS_TRANSLATIONS_DATABASE_URL env var accordingly.

    # Migrate database
    djangocms-helper djangocms_translations migrate --cms --extra-settings=tests/settings.py

    # Run server
    djangocms-helper djangocms_translations runserver --cms --extra-settings=tests/settings.py

    # In order to test the supertext integration:
    # 1) Set up a dev accont for supertext (https://dev.supertext.ch/en/signup) and use it
    # 2) Run server setting DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER and DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD env vars
