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
from asset.models import OnlineEvent, EC2Instance, SecurityGroupIsolated, \
    Region, EventLog
from ec2 import run_instances, add_instance_tags, add_volume_tags,\
    find_name_tag
from openfalcon import openfalcon_login, openfalcon_logout, openfalcon_enable, \
    openfalcon_disable


########################### PRE-DEFINED STEPS #################################
def step_disable_alarm(ec2_resource, instance_id):
    # read instance information:
    ec2instance = EC2Instance.objects.get(instance_id=instance_id)
    # log into openfalcon:
    try:
        session = openfalcon_login(
            settings.OPENFALCON['login_url'],
            settings.OPENFALCON['username'],
            settings.OPENFALCON['password'],
            settings.OPENFALCON['cert_file'],
            settings.OPENFALCON['cert_key']
        )
    except Exception as ex:
        return (False, "Failed to log into OpenFalcon.")
    # send request to disable alarm:
    result = openfalcon_disable(
        session, 
        settings.OPENFALCON['switch_url'],
        [ec2instance,]
    )
    if result.status_code != 200:
        return (False, "Failed to disable alarm.")
    # log out from openfalcon:
    result = openfalcon_logout(session, settings.OPENFALCON['logout_url'])
    if result.status_code != 200:
        return (False, "Failed to logout OpenFalcon.")
    return (True, "Alarm disabled.")


def step_enable_alarm(ec2_resource, instance_id):
    # read instance information:
    ec2instance = EC2Instance.objects.get(instance_id=instance_id)
    # log into openfalcon:
    try:
        session = openfalcon_login(
            settings.OPENFALCON['login_url'],
            settings.OPENFALCON['username'],
            settings.OPENFALCON['password'],
            settings.OPENFALCON['cert_file'],
            settings.OPENFALCON['cert_key']
        )
    except Exception as ex:
        return (False, "Failed to log into OpenFalcon.")
    # send request to disable alarm:
    result = openfalcon_enable(
        session, 
        settings.OPENFALCON['switch_url'],
        [ec2instance,]
    )
    if result.status_code != 200:
        return (False, "Failed to enable alarm.")
    # log out from openfalcon:
    result = openfalcon_logout(session, settings.OPENFALCON['logout_url'])
    if result.status_code != 200:
        return (False, "Failed to logout OpenFalcon.")
    return (True, "Alarm enabled.")


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
        new_instance.refresh_from_db()
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
def do_isolate(region, online_event):
    """Apply closed security group to resource"""
    global logger
    instance_id = online_event.resource_id
    # init boto3
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    ec2_resource = session.resource('ec2')
    # Disable alarm for this instance:
    logger.info("Disabling alarm for instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_disable_alarm')
    result = step_disable_alarm(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    if not result[0]:
        return result
    # Isolate old instance:
    logger.info("Isolating instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_isolate_instance')
    result = step_isolate_instance(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    return result
 

def do_restart(region, online_event):
    """Task to restart an instance (by stop and start, not reboot)"""
    global logger
    instance_id = online_event.resource_id
    # init boto3:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    ec2_resource = session.resource('ec2')
    # Disable alarm for this instance:
    logger.info("Disabling alarm for instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_disable_alarm')
    result = step_disable_alarm(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    if not result[0]:
        return result
    # stop instance:
    logger.info("Stopping instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_stop_instance')
    result = step_stop_instance(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    if not result[0]:
        return result
    # start instance
    logger.info("Starting instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_start_instance')
    result = step_start_instance(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    if not result[0]:
        return result
    # Re-enable alarm for this instance:
    logger.info("Re-enabling alarm for instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_enable_alarm')
    result = step_enable_alarm(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    return result


def do_replace(region, online_event):
    """Task to replace the instance with a new one."""
    global logger
    instance_id = online_event.resource_id
    # init boto3:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    ec2_resource = session.resource('ec2')
    # Start a new instance:
    logger.info("Starting new instance.")
    event_log = EventLog.get_event_log(online_event, 'step_run_instance')
    result = step_run_instance(ec2_resource, instance_id)
    #result = (True, "Auto success.")
    event_log.log_result(result)
    logger.info(result)
    if not result[0]:
        return result
    # Isolate old instance:
    logger.info("Isolating instance %s"%(instance_id,))
    event_log = EventLog.get_event_log(online_event, 'step_isolate_instance')
    result = step_isolate_instance(ec2_resource, instance_id)
    event_log.log_result(result)
    logger.info(result)
    return result
###############################################################################


def localtime_now():
    now = datetime.datetime.now()
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(now)

def main():
    def tempfunc(*args, **kwargs):
        print("do_replace")
        return (False, "Just kidding")

    actions = {
        'restart': do_restart,
        'replace': do_replace,
        #'replace': tempfunc,
        'isolate': do_isolate,
    }
    # Parse arguments:
    try:
        event_id = int(sys.argv[1])
        action = sys.argv[2]
    except:
        print("Usage: python worker.py <event_id> <action>")
        sys.exit(1)
    # Init mq:
    #try:
    #    mq_conn, mq_channel = get_mq_connection(
    #        settings.MQ_CONF,
    #        'worker'
    #    )
    #    logger.info("RabbitMQ connection established.")
    #except:
    #    logger.error("Failed to init RabbitMQ connection.")
    #    logger.error(traceback.format_exc())
    #    sys.exit(1)
    # Read and update event:
    online_event = OnlineEvent.objects.get(pk=event_id)
    if online_event.event_state != 'new':
        print "Event has been assigned. Exiting."
        return 
    region = online_event.region
    # Execute action:
    action_func = actions.get(action)
    if action_func is not None:
        # Perform action:
        result = action_func(region, online_event)
        # Record result:
        if result[0]:
            online_event.event_state = 'solved'
        else:
            online_event.event_state = 'error'
        online_event.result_detail = result[1]
        online_event.save()



if __name__ == '__main__':
    main()

