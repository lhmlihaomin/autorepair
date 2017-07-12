#!/usr/bin/python
"""
Perform recovery operations.
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

# add project dir to PYTHONPATH:
sys.path.append(
    os.path.abspath("..")
)

from notification.core import queue_notification
from asset.models import Region, OnlineEvent, EC2Instance

REGION = 'cn-north-1'


def step_stop_instance(ec2_resource, instance_id):
    """Step to stop an EC2 instance"""
    instance = ec2_resource.Instance(instance_id)
    if instance.state['Name'] != 'running':
        return (False, "Instance is not in running state.")
    else:
        instance.stop()
        # wait 4 x 30s = 2 minutes, until instance state turns "stopped":
        for i in range(4):
            instance.reload()
            if instance.state['Name'] == 'stopped':
                return (True, "Instance has been stopped.")
            time.sleep(30)
        return (False, "Instance stop timed out.")

def step_start_instance(ec2_resource, instance_id):
    """Step to start an EC2 instance"""
    instance = ec2_resource.Instance(instance_id)
    if instance.state['Name'] != 'stopped':
        return (False, "Instance is not in stopped state.")
    else:
        instance.start()
        # wait at most 2 minutes:
        for i in range(4):
            instance.reload()
            if instance.state['Name'] == 'running':
                return (True, "Instance has been started.")
            time.sleep(30)
        return (False, "Instance start timed out.")


def do_restart(region, instance_id):
    print("Will restart instance %s in region %s"%(
        instance_id, 
        region.name
    ))
    return (True, "")
    # init boto3:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    resource = session.resource('ec2')
    # stop instance:
    print("Stopping instance %s"%(instance_id,))
    result = step_stop_instance(resource, instance_id)
    print result
    if not result[0]:
        return result
    # start instance
    print("Starting instance %s"%(instance_id,))
    result = step_start_instance(resource, instance_id)
    return result


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
    return (mq_conn, mq_channel)


def main():
    actions = {
        'restart': do_restart
    }
    # parse arguments:
    try:
        event_id = int(sys.argv[1])
        action = sys.argv[2]
    except:
        print("Usage: python demo.py <event_id>")
        sys.exit(0)
    # read and update event:
    online_event = OnlineEvent.objects.get(pk=event_id)
    region = online_event.region
    # execute action:
    print("Restart instance %s in region %s"%(
        online_event.resource_id,
        region.name
    ))
    action_func = actions[action]
    result = action_func(region, online_event.resource_id)
    # write back result:
    online_event.event_state = str(result[0])
    online_event.result_detail = result[1]
    online_event.save()
    # send result notification:
    queue_notification(channel, online_event.to_dict())


if __name__ == "__main__":
    main()
