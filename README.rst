=======================
django CMS Translations
=======================


|pypi| |build| |coverage|

**django CMS Translations** enables content, created in django CMS, to be
transferred to an external translation tool, processed and send back. It
automatically creates the necessary plugin structure from the translations.

This addon is compatible with `Divio Cloud <http://divio.com>`_ and is also available on the
`django CMS Marketplace <https://marketplace.django-cms.org/en/addons/browse/djangocms-translations/>`_
for easy installation.


Contributing
============

This is a an open-source project. We'll be delighted to receive your
feedback in the form of issues and pull requests. Before submitting your
pull request, please review our `contribution guidelines
<http://docs.django-cms.org/en/latest/contributing/index.html>`_.


Documentation
=============

See ``REQUIREMENTS`` in the `setup.py <https://github.com/divio/djangocms-translations/blob/master/setup.py>`_
file for additional dependencies:

* Python 2.7, 3.4 or higher
* Django 1.11 or higher
* django CMS 3.5 or higher


Installation
------------

For a manual install:

* run ``pip install djangocms-translations``
* add ``djangocms_translations`` to your ``INSTALLED_APPS``
* run ``python manage.py migrate djangocms_translations``


Configuration
-------------

**When content is sent for translation, the source pages must not be edited
until the translated content has been written back successfully.**

The translation system needs to find exactly the same plugins in the content
as were there when the process was initiated. If any are missing, it will
cause an error and require the process to be restarted.

**This affects all plugins on a page** including text, images and other plugin types.

**Any change to plugins on a source page while content is out for translation
can cause write-back failures.**

Single page translation
#######################

You find the single page translation feature under Translation > Translate this page
provided that there is one or more language present to be translated to.
The language displayed in that step represent the current available and configured
languages of the current site. Do not worry about this too much as you will be
able to customise the selection in the next step:

**Configuring the translation request**
The single translation request, unlike the bulk translation request, allows you
to translate a single page from one source page to another across the multisite
setup. The following options are available:

**Source CMS Page**
This is the source page you need to select. It is represented by the site
from the multisite setup and the page that should be selected for translatation.

**Source Language**
This step will always show the fully-configured languages available in the system.
You need to check in advance the page tree which page and language you would like to pick. This step can lead to errors if the source page is not configured, or has no content.

**Target CMS Page**
This is the target page you need to select. The interface is the same as on the
Source CMS Page. It is important that the targeted CMS Page is configured and
has no content. If the target page has already content, the new translated content
will be appended to the current one. The translation system will never replace/erase content.

**Target Language**
This behaves the same as the Source Language. Also in this case, make sure that
you select the correct language from the target source. If it is another site
you need to check in advance that the language is available otherwise you will
receive an error.

**Provider Backend**
Select the translation service. As of now only
`Supertext <https://www.supertext.ch>`_ is supported.

Once the translation request has been sent, the Status, as described under
Overview will apply. If there are issues you may want to check with the
translation provider on their status.

Bulk translation
################

Unlike the single page translation feature, bulk translation only allows to
translate on the current site you have selected. The following options are
available:

**Source Language**
Similar to the single translation request you need to select a source language.
Note that all configured language options in the systems will be shown, not just
the ones for the current site. So, you need to be aware of what languages the
current site has, and select the correct source language.

**Target Language**
Similar to the single translation request; you need to select a target language.
Once again all configured language options in the systems are available, and you
need to be aware of what languages the current site has, and select the correct
source language. The target language needs also to be configured, otherwise the
full bulk translation will fail, even if just one page is not configured correctly.

**Provider Backend**
Same as for single translation requests.

Settings
########

With ``DJANGOCMS_TRANSLATIONS_CONF`` you can define what data should be
sent from any given plugin to control unnecessary data isn't transferred::

    DJANGOCMS_TRANSLATIONS_CONF = {
        'TextPlugin': {'fields': ['body']},
        'LinkPlugin': {'fields': ['name']},
        'AudioFilePlugin': {'fields': ['text_title', 'text_description']},
        'AudioFolderPlugin': {'fields': []},
        'AudioTrackPlugin': {'fields': ['label']},
        'AudioPlayerPlugin': {'fields': ['label']},
        'FilePlugin': {'fields': ['link_title']},
        'PicturePlugin': {'fields': ['caption_text']},
        'VideoTrackPlugin': {'fields': ['label']},
        'VideoSourcePlugin': {'fields': ['text_title', 'text_description']},
        'VideoPlayerPlugin': {'fields': ['label']},
    }

With ``DJANGOCMS_TRANSLATIONS_USE_STAGING`` set to ``True`` you can send the
data to a staging environment rather than live.

With ``DJANGOCMS_TRANSLATIONS_BULK_BATCH_SIZE`` you can define the batch size
to be transmitted to the translation provider. The default is ``100``.


Running Tests
-------------

You can run tests by executing::

    virtualenv env
    source env/bin/activate
    pip install -r tests/requirements.txt
    python setup.py test


.. |pypi| image:: https://badge.fury.io/py/djangocms-translations.svg
    :target: http://badge.fury.io/py/djangocms-translations
.. |build| image:: https://travis-ci.org/divio/djangocms-translations.svg?branch=master
    :target: https://travis-ci.org/divio/djangocms-translations
.. |coverage| image:: https://codecov.io/gh/divio/djangocms-translations/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/divio/djangocms-translations
