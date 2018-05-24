# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-24 11:54
from __future__ import unicode_literals

from django.db import migrations


def generate_provider_order_names(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    TranslationRequest = apps.get_model('djangocms_translations', 'TranslationRequest')

    requests = TranslationRequest.objects.using(db_alias).filter(
        provider_order_name='',
    )
    for request in requests:
        request.provider_order_name = request.order.request_content.get('OrderName')
        request.save(update_fields=('provider_order_name',))


class Migration(migrations.Migration):

    dependencies = [
        ('djangocms_translations', '0006_translationrequest_provider_order_name'),
    ]

    operations = [
        migrations.RunPython(
            generate_provider_order_names,
            lambda *args, **kwargs: None,
        ),
    ]
