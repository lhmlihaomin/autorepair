# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-19 03:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0008_ec2instance_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='ec2instance',
            name='last_checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]