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

from_address = None
to_addresses = None
ses_client = None


def send_mail(subject, body):
    global ses_client
    global from_address
    global to_addresses
    response = ses_client.send_email(
        Source=from_address,
        Destination={
            'ToAddresses': to_addresses
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
    return response


def send_notification_mail(event):
    subject = "[AUTOREPAIR] New Event"
    body = ""
    for key in event.keys():
        body += "%s: \t%s\r\n"%(key, str(event[key]))
    return send_mail(subject, body)


def send_exception_mail(exception):
    subject = "[AUTOREPAIR] Exception"
    body = str(exception)
    return send_mail(subject, body)


def notification_handler(ch, method, props, body):
    print("[NOTIFICATION] "+body)
    #return True
    #try:
    event = json.loads(body)
    response = send_notification_mail(event)
    print(response)
    #except:
        # log exception
    #    pass
    

def exception_handler(ch, method, props, body):
    print("[EXCEPTION] "+body)
    #return True
    #try:
    exception = json.loads(body)
    response = send_exception_mail(exception)
    print(response)
    #except:
        # log exception
    #    pass


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
        queue="q_notification",
        no_ack=True
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
        queue="q_exception",
        no_ack=True
    )
    return (mq_conn, mq_channel)


def init_ses(conf_file_path):
    global from_address
    global to_addresses

    with open(conf_file_path, 'r') as conffile:
        conf = json.loads(conffile.read())
    profile_name = conf['profile_name']
    region_name = conf['region_name']
    from_address = conf['from_address']
    to_addresses = conf['to_addresses']

    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    ses_client = session.client('ses')
    return ses_client
    

def main():
    global ses_client
    mq_conf_file = "../conf/mq.conf.json"
    ses_conf_file = "../conf/ses.conf.json"
    try:
        ses_client = init_ses(ses_conf_file)
        mq_conn, mq_channel = init_mq(mq_conf_file)
        print("Start consuming ...")
        mq_channel.start_consuming()
    except KeyboardInterrupt:
        print("Bye.")
        mq_conn.close()


if __name__ == "__main__":
    main()
