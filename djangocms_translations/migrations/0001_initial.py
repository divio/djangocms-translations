# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-09-08 07:56
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import cms.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cms', '0016_auto_20160608_1535'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TranslationOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_translated', models.DateTimeField(blank=True, null=True)),
                ('state', models.CharField(choices=[('open', 'Open'), ('pending_quote', 'Pending'), ('failed', 'Failed/cancelled'), ('done', 'Done')], default='open', max_length=100)),
                ('request_content', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('response_content', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('provider_details', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='TranslationQuote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_received', models.DateTimeField()),
                ('name', models.CharField(max_length=1000)),
                ('description', models.TextField(blank=True, default='')),
                ('delivery_date', models.DateTimeField(blank=True, null=True)),
                ('price_currency', models.CharField(max_length=10)),
                ('price_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('provider_options', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='TranslationRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('draft', 'Draft'), ('open', 'Open'), ('pending_quote', 'Pending quote from provider'), ('pending_approval', 'Pending approval of quote'), ('ready_for_submission', 'Pending submission to translation provider'), ('in_translation', 'In translation'), ('ready_for_import', 'Ready for import'), ('imported', 'Imported'), ('cancelled', 'Cancelled')], default='draft', max_length=100)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_submitted', models.DateTimeField(blank=True, null=True)),
                ('date_received', models.DateTimeField(blank=True, null=True)),
                ('date_imported', models.DateTimeField(blank=True, null=True)),
                ('source_language', models.CharField(max_length=10)),
                ('target_language', models.CharField(max_length=10)),
                ('provider_backend', models.CharField(choices=[('SupertextTranslationProvider', 'Supertext')], max_length=100)),
                ('provider_options', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('export_content', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('request_content', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('cms_page', cms.models.fields.PageField(on_delete=django.db.models.deletion.CASCADE, to='cms.Page')),
                ('selected_quote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='djangocms_translations.TranslationQuote')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='translationquote',
            name='request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to='djangocms_translations.TranslationRequest'),
        ),
        migrations.AddField(
            model_name='translationorder',
            name='request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order', to='djangocms_translations.TranslationRequest'),
        ),
    ]
