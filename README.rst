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


Please note you need a postgres database running for this to work.

Add ``djangocms_translations`` to ``INSTALLED_APPS``.

Developing via DjangoCMS-helper
-------------------

::

    # Add a POSTGRES database (below I'm using user=password=database_name=djangocmstranslations)

    # Migrate django.contrib.sites app (yes, we need this app to migrate before the others)
    DATABASE_URL=postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations djangocms-helper django.contrib.sites migrate --cms --extra-settings=tests/settings.py

    # Migrate our app per se
    DATABASE_URL=postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations djangocms-helper djangocms_translations migrate --cms --extra-settings=tests/settings.py

    # Set up a dev accont for supertext (https://dev.supertext.ch/en/signup) and use it
    DATABASE_URL=postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER=XXX DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD=XXX djangocms-helper djangocms_translations runserver --cms --extra-settings=tests/settings.py


Running tests
-------------------

::

    # Assuming you're using postgres user=password=database_name=djangocmstranslations
    DATABASE_URL=postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations make test


Running tox
-------------------

::

    # Assuming you're using postgres user=password=database_name=djangocmstranslations
    DATABASE_URL=postgres://djangocmstranslations:djangocmstranslations@localhost:5432/djangocmstranslations DJANGOCMS_TRANSLATIONS_SUPERTEXT_USER=XXX DJANGOCMS_TRANSLATIONS_SUPERTEXT_PASSWORD=XXX tox
