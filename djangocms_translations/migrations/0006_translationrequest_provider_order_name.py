# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-24 11:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djangocms_translations', '0005_auto_20180208_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='translationrequest',
            name='provider_order_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
