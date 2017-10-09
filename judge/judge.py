#!/usr/bin/python
"""
"Judge" app consumes from RabbitMQ queues and dispatch each message to an 
individual worker process.
The message is first analyzed to find out its type and affected resource. If 
this event can be resolved by automated worker procedure, a worker process
is started. If not, the message is ignored.

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

import json
import time
import subprocess
import traceback
import logging
logger = logging.getLogger('judge')

from lib_msg_q import init_mq
from asset.models import Region, OnlineEvent, EC2Instance, EventHandleRule
from lib_msg_q import get_mq_connection

########################## Callbacks ##########################################
def callback_events_ec2(channel, method, props, body):
    """Consume events and take actions."""
    # parse message as JSON string:
    try:
        event = json.loads(body)
        # lookup module info:
        online_event = OnlineEvent.objects.get(pk=event['event_id'])
        print 'EVENT_EC2: '+online_event.event_type
    except Exception as ex:
        # log exception
        print(ex,)
        return False
    start_worker(online_event)
###############################################################################


def start_worker(online_event):
    """
    Start a worker process to handle OnlineEvent.

    Parameters
    ---
    online_event: json obj
    """
    # read information:
    if online_event.resource_type == 'EC2':
        try:
            instance = EC2Instance.objects.get(
                instance_id=online_event.resource_id
            )
            module = instance.module
        except EC2Instance.DoesNotExist:
            # TODO: log exception
            return
    # make decision:
    try:
        rule = EventHandleRule.objects.get(
            module_name=module.name,
            event_type=online_event.event_type
        )

    except:
        # rule not found, do nothing:
        return 
    # start workers if necessary:
    worker_path = os.path.sep.join([
        settings.PROJECT_DIR,
        'worker',
        'worker.py'
    ])
    
    args = [
        'python',
        worker_path,
        str(online_event.id),
        rule.handler
    ]
    subprocess.Popen(args)


def main():
    # Judge module callbacks:
    callbacks = {
        'callback_events_ec2': callback_events_ec2
    }
    try:
        mq_conn, mq_channel = get_mq_connection(
            settings.MQ_CONF, 
            'judge', 
            callbacks=callbacks
        )
        logger.info("RabbitMQ connection established.")
    except Exception as ex:
        logger.error("Failed to init RabbitMQ connection.")
        logger.error(traceback.format_exc())
        sys.exit(1)

    try:
        logger.info("Start consuming.")
        mq_conn.close()
        #mq_channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt. Stopping.")
        print("")
        print("Bye.")
        mq_conn.close()
        sys.exit(0)


if __name__ == '__main__':
    main()
