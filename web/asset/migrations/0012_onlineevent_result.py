# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-07 09:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0011_ec2instance_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='onlineevent',
            name='result',
            field=models.CharField(default='pending', max_length=10),
        ),
    ]
