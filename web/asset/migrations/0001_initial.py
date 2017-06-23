# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-06-09 07:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EC2Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField()),
                ('active', models.BooleanField(default=True)),
                ('last_update_time', models.DateTimeField()),
                ('name', models.CharField(max_length=500)),
                ('instance_id', models.CharField(max_length=500)),
                ('username', models.CharField(max_length=100)),
                ('private_ip_address', models.CharField(max_length=500)),
                ('key_pair', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='ELB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField()),
                ('active', models.BooleanField(default=True)),
                ('last_update_time', models.DateTimeField()),
                ('name', models.CharField(max_length=500)),
                ('dns_name', models.CharField(max_length=500)),
                ('scheme', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('version', models.CharField(max_length=500)),
                ('launch_config', models.TextField()),
                ('service_type', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('tag_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=500)),
            ],
        ),
        migrations.AddField(
            model_name='module',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Region'),
        ),
        migrations.AddField(
            model_name='elb',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Module'),
        ),
        migrations.AddField(
            model_name='elb',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Region'),
        ),
        migrations.AddField(
            model_name='ec2instance',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Module'),
        ),
        migrations.AddField(
            model_name='ec2instance',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.Region'),
        ),
    ]
