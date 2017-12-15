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

    # We need djangocms-transfer
    git clone git@github.com:divio/djangocms-transfer.git ../djangocms-transfer
    cd ../djangocms-transfer
    python setup.py install

    # We need django-cms DEVELOP branch
    git clone git@github.com:divio/django-cms.git ../django-cms
    cd ../django-cms
    git checkout develop
    python setup.py install

Add ``djangocms_translations`` to ``INSTALLED_APPS``.
