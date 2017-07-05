#!/usr/bin/python
"""Comsumes mesages and send messages to users."""
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

ses_client = None

def send_mail(from_address, to_address, subject, body):
    global ses_client
    response = client.send_email(
        Source=from_address,
        Destination={
            'ToAddresses': [
                to_address,
            ]
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8',
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8',
                }
            }
        },
    )
    print response


def send_notification_mail():
    pass


def send_exception_mail():
    pass


def notification_handler(ch, method, props, body):
    print("[NOTIFICATION] "+body)
    return True
    try:
        event = json.loads(body)
    except:
        # log exception
        pass
    


def exception_handler(ch, method, props, body):
    print("[EXCEPTION] "+body)
    return True
    pass


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
    # declare exchange:
    print("Declaring exchange ...")
    mq_channel.exchange_declare(
        exchange="topic_notifications",
        type="topic"
    )
    # declare & bind notification queue:
    print("Declaring queue notification ...")
    mq_channel.queue_declare(
        queue="q_notification",
        durable=True
    )
    mq_channel.queue_bind(
        queue="q_notification",
        exchange="topic_notifications",
        routing_key="notifications.notification.#"
    )
    mq_channel.basic_consume(
        notification_handler,
        queue="q_notification"
    )
    # declare & bind exception queue:
    print("Declaring queue exception ...")
    mq_channel.queue_declare(
        queue="q_exception",
        durable=True
    )
    mq_channel.queue_bind(
        queue="q_exception",
        exchange="topic_notifications",
        routing_key="notifications.exception.#"
    )
    mq_channel.basic_consume(
        exception_handler,
        queue="q_exception"
    )
    return (mq_conn, mq_channel)


"""
session = boto3.Session(profile_name=profile_name, region_name=region_name)
client = session.client('ses')

response = client.send_email(
    Source=FROM_ADDRESS,
    Destination={
        'ToAddresses': [
            TO_ADDRESS,
        ]
    },
    Message={
        'Subject': {
            'Data': 'SES Mail Test',
            'Charset': 'UTF-8',
        },
        'Body': {
            'Text': {
                'Data': 'Plain text mail body.',
                'Charset': 'UTF-8',
            }
        }
    },
)
"""


def main():
    mq_conf_file = "../conf/mq.conf.json"
    try:
        mq_conn, mq_channel = init_mq(mq_conf_file)
        print("Start consuming ...")
        mq_channel.start_consuming()
    except KeyboardInterrupt:
        print("Bye.")
        mq_conn.close()


if __name__ == "__main__":
    main()
