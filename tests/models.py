from cms.models import CMSPlugin
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class DummyText(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
        parent_link=True,
    )
    body = models.TextField()

    class Meta:
        abstract = False

    def __str__(self):
        return 'dummy text object'


@python_2_unicode_compatible
class DummyLink(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
        parent_link=True,
    )
    label = models.TextField()

    class Meta:
        abstract = False

    def __str__(self):
        return 'dummy link object'
