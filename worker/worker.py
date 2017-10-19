#!/usr/bin/python
# -*- encoding:utf8 -*-
"""
Worker is started by the "judge" module and is used to resolve online events 
by pre-defined steps.

Author: lihaomin@tp-link.com.cn
"""
__version__ = '0.0.1'

###############################################################################
# DJANGO SETUP
import os
import sys
import django
parent_path = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
django_path = os.path.sep.join([
    parent_path,
    'web'
])
sys.path.append(parent_path)
sys.path.append(django_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
django.setup()

from django.conf import settings
###############################################################################

import datetime
import time
import pytz
import json
import traceback
import logging
logger = logging.getLogger('worker')

import boto3

from lib_msg_q import get_mq_connection
from notification.core import queue_notification
from asset.models import Region, OnlineEvent, EC2Instance, SecurityGroupIsolated
from ec2 import run_instances, add_instance_tags, add_volume_tags,\
    find_name_tag


########################### PRE-DEFINED STEPS #################################
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


def step_run_instance(ec2_resource, instance_id):
    """Launch a new instance similar to the given one."""
    # Read instance info:
    ec2instance = EC2Instance.objects.get(instance_id=instance_id)
    module = ec2instance.module
    # Launch instance:
    instances = run_instances(ec2_resource, module, 1)
    instance_ids = [instance.id for instance in instances]
    # Add instance tags:
    add_instance_tags(ec2_resource, module, instance_ids)
    add_volume_tags(ec2_resource, instance_ids)
    instance = instances[0]
    instance.reload()   # refresh instance data to get tags
    new_instance = EC2Instance(
        module=module,
        region=module.region,
        status=False,
        active=True,
        #last_update_time=localtime_now(),
        created_at=localtime_now(),
        name=find_name_tag(instance),
        instance_id=instance.id,
        username='ubuntu',
        private_ip_address=instance.private_ip_address,
        key_pair=instance.key_pair.name
    )
    new_instance.save()

    # Wait for instance to turn OK (3 minutes at most):
    # (Background checker should check instance status every 1 minute or 2)
    for i in range(5):
        time.sleep(30)
        if new_instance.status:
            return (True, "New instance started.")
    # Return false when instance check fails:
    return (False, "Instance failed status check.")



def step_isolate_instance(ec2_resource, instance_id):
    """Apply restrictive security group to the given instance."""
    try:
        # Read instance & vpc_id:
        instance = ec2_resource.Instance(instance_id)
        vpc_id = instance.vpc_id
        # Get the closed security group:
        group_closed = SecurityGroupIsolated.get_by_vpc_id(vpc_id)
        # Replace instance security group with closed group:
        result = instance.modify_attribute(
            Groups=[
                group_closed.group_id,
            ]
        )
        return (True, "Instance security group isolated.")
    except Exception as ex:
        return (False, ex.message)
###############################################################################


############################## TASK FUNCTIONS #################################
def do_restart(region, instance_id):
    """Task to restart an instance (by stop and start, not reboot)"""
    # init boto3:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    ec2_resource = session.resource('ec2')
    # stop instance:
    print("Stopping instance %s"%(instance_id,))
    result = step_stop_instance(ec2_resource, instance_id)
    print result
    if not result[0]:
        return result
    # start instance
    print("Starting instance %s"%(instance_id,))
    result = step_start_instance(ec2_resource, instance_id)
    return result


def do_replace(region, instance_id):
    """Task to replace the instance with a new one."""
    # init boto3:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    ec2_resource = session.resource('ec2')
    # Start a new instance:
    result = step_run_instance(ec2_resource, instance_id)
    if not result[0]:
        return result
    # Isolate old instance:
    result = step_isolate_instance(ec2_resource, instance_id)
    return result
###############################################################################


def localtime_now():
    now = datetime.datetime.now()
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(now)

def main():
    actions = {
        'restart': do_restart,
        'replace': do_replace,
    }
    # Parse arguments:
    try:
        event_id = int(sys.argv[1])
        action = sys.argv[2]
    except:
        print("Usage: python worker.py <event_id> <action>")
        sys.exit(1)
    # Init mq:
    try:
        mq_conn, mq_channel = get_mq_connection(
            settings.MQ_CONF,
            'worker'
        )
        logger.info("RabbitMQ connection established.")
    except:
        logger.error("Failed to init RabbitMQ connection.")
        logger.error(traceback.format_exc())
        sys.exit(1)
    # Read and update event:
    online_event = OnlineEvent.objects.get(pk=event_id)
    region = online_event.region
    # Execute action:
    action_func = actions.get(action)
    if action_func is not None:
        result = action_func(region, online_event.resource_id)


def testmain():
    ###
    region = Region.objects.get(name='cn-north-1')
    #session = boto3.Session(profile_name='cn-alpha', region_name='cn-north-1')
    #resource = session.resource('ec2')
    #ec2_resource = resource
    ###
    instance_id = 'i-06fc08b83286621d9'
    ec2instance = EC2Instance.objects.get(instance_id=instance_id)
    result = do_replace(region, instance_id)

    print(result)

if __name__ == '__main__':
    main()

