#!/usr/bin/python
"""
Consumes events. Decide what actions should be taken on an event.
Demo code.
"""
###############################################################################
# DJANGO SETUP
import os
import sys
import django
django_path = os.path.abspath(
    os.path.sep.join((os.path.dirname(__file__), '..', 'web',))
)
sys.path.append(django_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
django.setup()
###############################################################################

import json
import time

import boto3
import pika

from asset.models import Region, OnlineEvent

REGION = 'cn-north-1'

def init_mq(conf_file_path):
    with open(conf_file_path, 'r') as conffile:
        conf = json.loads(conffile.read())
    mq_conn = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=conf['host'],
            port=int(conf['port']),
            credentials=pika.PlainCredentials(
                conf['username'],
                conf['password']
            )
        )
    )
    mq_channel = mq_conn.channel()
    for exchange in conf['exchanges']:
        print("Declaring exchange %s:%s"%(exchange['name'], exchange['type']))
        mq_channel.exchange_declare(
            exchange=exchange['name'],
            type=exchange['type']
        )
    return (mq_conn, mq_channel)


def main():
    mq_conf_file = "../conf/mq.conf.json"
    region = Region.objects.get(name=REGION)
