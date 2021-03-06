# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-25 20:01
from __future__ import unicode_literals

import django_intenum
from django.db import migrations, models

import hsreplaynet.uploads.models


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0005_auto_20170122_1955'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='redshiftstagingtracktable',
            name='deduplication_complete',
        ),
        migrations.RemoveField(
            model_name='redshiftstagingtracktable',
            name='duplicates_removed',
        ),
        migrations.RemoveField(
            model_name='redshiftstagingtracktable',
            name='insert_count',
        ),
        migrations.RemoveField(
            model_name='redshiftstagingtracktable',
            name='insert_duration_seconds',
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='close_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='deduplicating_ended_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='deduplicating_started_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='gathering_stats_ended_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='gathering_stats_started_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtrack',
            name='stage',
            field=django_intenum.IntEnumField(default=1, enum=hsreplaynet.uploads.models.RedshiftETLStage),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='analyze_query_handle',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='dedupe_query_handle',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='deduplication_ended_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='deduplication_started_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='gathering_stats_ended_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='gathering_stats_handle',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='gathering_stats_started_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='insert_query_handle',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='stage',
            field=django_intenum.IntEnumField(default=1, enum=hsreplaynet.uploads.models.RedshiftETLStage),
        ),
        migrations.AddField(
            model_name='redshiftstagingtracktable',
            name='vacuum_query_handle',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
