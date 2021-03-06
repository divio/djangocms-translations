# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-08 19:56
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models

import cms.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0018_pagenode'),
        ('djangocms_translations', '0004_auto_20171219_1209'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranslationRequestItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_cms_page', cms.models.fields.PageField(on_delete=django.db.models.deletion.CASCADE, related_name='translation_requests_as_source', to='cms.Page')),
                ('target_cms_page', cms.models.fields.PageField(on_delete=django.db.models.deletion.CASCADE, related_name='translation_requests_as_target', to='cms.Page')),
            ],
        ),
        migrations.RemoveField(
            model_name='translationrequest',
            name='source_cms_page',
        ),
        migrations.RemoveField(
            model_name='translationrequest',
            name='target_cms_page',
        ),
        migrations.AddField(
            model_name='translationrequestitem',
            name='translation_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='djangocms_translations.TranslationRequest'),
        ),
    ]
