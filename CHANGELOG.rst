=========
Changelog
=========

1.4.0 (unreleased)
==================

* Added support for Django 2.0 and 2.1
* Adapted test matrix
* Cleaned up files


1.3.7 (2018-09-06)
==================

* Hide bulk translations menu if number of languages for that site == 1
* Show page-to-page translations menu even when current page has only one language (use settings.LANGUAGES as a pivot)
* Add Django 1.11 compatibility


1.3.6 (2018-08-14)
==================

* Fix another language codes mismatch on supertext


1.3.5 (2018-08-13)
==================

* Fix language codes mismatch on supertext for languages "pl" and "it"


1.3.4 (2018-06-26)
==================

* Show proper language names in toolbar menu
* Show proper urls for pages from other sites then current


1.3.3 (2018-06-22)
==================

* Fixed a bug where order ID wasn't displayed on certain operations


1.3.2 (2018-06-20)
==================

* Changed quotes endpoint to v1 again for supertext.
* Changed orders endpoint to v1.1 for supertext.


1.3.1 (2018-06-20)
-----------------

* Changed quotes endpoint to v1.1 for supertext. All others continue as v1


1.3.0 (2018-06-20)
-----------------

* Changed all supertext endpoints to use version 1.1
* Fixed a bug preventing a translation request from being retried


1.2.3 (2018-06-19)
-----------------

* Fixed a bug where the page tree would render incomplete


1.2.2 (2018-06-15)
==================

* Cosmetic changes to translations UI


1.2.1 (2018-06-12)
==================

* Fixed a bug with migration 0008 with requests without order


1.2.0 (2018-06-12)
==================

* Added send without quote functionality to bulk translation requests
* Added error logging


1.1.3 (2018-02-22)
==================

* Avoid multiple form submissions when choosing a quote


1.1.2 (2018-02-19)
==================

* Improve bulk translations UX


1.1.1 (2018-02-19)
==================

* Improve bulk translations UX


1.1.0 (2018-02-15)
==================

* Add bulk translations support


1.0.0 (2018-01-29)
==================

* Initial release
