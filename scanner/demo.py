#!/usr/bin/python
"""
Scan for online events.
Basic functions.
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
    

def get_events(region):
    session = boto3.Session(
        profile_name=region.profile_name, 
        region_name=region.name
    )
    ec2client = session.client('ec2')
    response = ec2client.describe_instance_status()
    statuses = response['InstanceStatuses']
    events = []
    for status in statuses:
        if status.has_key('Events'):
            #ret.append({'instance_id': status['InstanceId'], 'event': status['Events'][0],})
            events.append({
                'source': 'instance_status',
                'resource_type': 'EC2',
                'resource_id': status['InstanceId'],
                'event_type': status['Events'][0]['Code'],
                'detail': status['Events'][0]['Description'],
            })
    return events


def create_event(event, channel):
    try:
        # test if event already exists:
        OnlineEvent.objects.get(resource_id=event['resource_id'], event_type=event['event_type'])
        print("Event already exists.")
    except:
        # create event in database:
        online_event = OnlineEvent()
        online_event.source = event['source']
        online_event.resource_type = event['resource_type']
        online_event.resource_id = event['resource_id']
        online_event.event_type = event['event_type']
        online_event.detail = event['detail']
        online_event.event_state = ""
        online_event.result_detail = ""
        online_event.save()
        # publish event to MQ:
        event.update({'event_id': online_event.id})
        channel.basic_publish(
            exchange="topic_events",
            routing_key="events.ec2."+event['event_type'],
            body=json.dumps(event)
        )



def main():
    mq_conf_file = "../conf/mq.conf.json"
    region = Region.objects.get(name=REGION)

    mq_conn, mq_channel = init_mq(mq_conf_file)
    events = get_events(region)
    for event in events:
        create_event(event, mq_channel)



if __name__ == "__main__":
    main()
