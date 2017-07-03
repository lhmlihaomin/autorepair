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
current_path = os.path.dirname(__file__)
if len(current_path) == 0:
    current_path = "."
django_path = os.path.abspath(
    os.path.sep.join((current_path, '..', 'web',))
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
    for queue in conf['queues']:
        mq_channel.queue_declare(
            queue=queue['name'],
            durable=True
        )
        mq_channel.queue_bind(
            queue=queue['name'],
            exchange=queue['exchange'],
            routing_key=queue['routing_key']
        )
        mq_channel.basic_consume(
            event_handler,
            queue=queue['name']
        )
    return (mq_conn, mq_channel)


def event_handler(channel, method, props, body):
    """Consume events and take actions."""
    # parse message as JSON string:
    # lookup module info:
    # make decision:
    # trigger notification:
    # start workers if necessary:
    pass


def main():
    # read conf:
    mq_conf_file = "../conf/mq.conf.json"
    region = Region.objects.get(name=REGION)
    mq_conn, mq_channel = init_mq(mq_conf_file)
    try:
        print("Start consuming ...")
        mq_channel.start_consuming()
    except KeyboardInterrupt:
        mq_conn.close()
        print("")
        print("Bye.")


if __name__ == "__main__":
    main()
