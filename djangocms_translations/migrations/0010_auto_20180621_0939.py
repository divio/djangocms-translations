# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-24 11:54
from __future__ import unicode_literals

from django.db import migrations


def fill_provider_order_ids_in_translation_orders(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    TranslationOrder = apps.get_model('djangocms_translations', 'TranslationOrder')

    orders = TranslationOrder.objects.using(db_alias).filter(provider_order_id='')
    for order in orders:
        order.provider_order_id = order.provider_details.get('Id') or order.response_content.get('Id')
        if order.provider_order_id:
            order.save(update_fields=('provider_order_id',))


class Migration(migrations.Migration):

    dependencies = [
        ('djangocms_translations', '0009_translationorder_provider_order_id'),
    ]

    operations = [
        migrations.RunPython(
            fill_provider_order_ids_in_translation_orders,
            migrations.RunPython.noop,
        ),
    ]
