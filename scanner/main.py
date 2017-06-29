#!/usr/bin/python
"""
Scanner module searches for abnormal events about online resources.
If an event is detected, it is then pushed into the MQ for judge module to 
analyse.
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
import signal

import boto3
import pika

from checks import InstanceStatusChecker
from asset.models import Region, OnlineEvent

# Constants:
REGION_NAME = 'cn-north-1'
"""
region = Region.objects.get(name=REGION_NAME)
events = get_events(region)
print_events(events)
exit()
"""

class Scanner(object):
    """Scans for online events."""
    def __init__(self, mq_conf_file_path):
        """Read configuration and make connections"""
        self.alive = True
        self.conf = None
        self.mq_conn = None
        self.mq_channel = None
        self.conf = {}
        try:
            with open(mq_conf_file_path, 'r') as conffile:
                self.conf['rabbitmq'] = json.loads(conffile.read())
        except Exception as ex:
            print ex
            sys.exit(1)
        self._init_rabbitmq()

    def _init_rabbitmq(self):
        self.mq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.conf['rabbitmq']['host'],
                port=int(self.conf['rabbitmq']['port']),
                credentials=pika.PlainCredentials(
                    self.conf['rabbitmq']['username'],
                    self.conf['rabbitmq']['password']
                )
            )
        )
        self.mq_channel = self.mq_conn.channel()

    def exit_handler(self, signum, frame):
        sys.stdout.write("Die now.\n")
        self.alive = False

    def create_event_db(self):
        pass

    def create_event_mq(self):
        pass

    def main_loop(self):
        while self.alive:
            sys.stdout.write(str(self.alive)+"\n")
            # do stuff:
            sys.stdout.write("Doing stuff ...\n")
            #checker = InstanceStatusChecker(region)
            # Small sleep interval, faster response to "kill":
            i = 0
            while i < 3:
                sys.stdout.write(str(i)+"\n")
                time.sleep(1)
                if not self.alive:
                    break
                i += 1


def main():
    mq_conf_file = os.path.sep.join((
        os.path.dirname(__file__), 
        '..', 
        'conf',
        'mq.conf.json'
    ))
    scanner = Scanner(mq_conf_file)
    signal.signal(signal.SIGINT, scanner.exit_handler)
    signal.signal(signal.SIGTERM, scanner.exit_handler)
    #signal.signal(signal.CTRL_C_EVENT, scanner.exit_handler)
    scanner.main_loop()


if __name__ == "__main__":
    main()
