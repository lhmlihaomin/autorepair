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

from checks import get_events, print_events
from asset.models import Region

# Constants:
REGION_NAME = 'cn-north-1'

#region = Region.objects.get(name=REGION_NAME)
#events = get_events(region)
#print_events(events)


class Scanner(object):
    """Scans for online events."""
    def __init__(self, conf_file_path):
        """Read configuration and make connections"""
        self.alive = True
        self.conf = None
        self.mq_conn = None
        self.mq_channel = None
        """try:
            with open(conf_file_path, 'r') as conffile:
                self.conf = json.loads(conffile.read())
        except Exception as ex:
            print ex
            sys.exit(1)
        self._init_rabbitmq()"""

    def _init_rabbitmq(self):
        self.mq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.conf['rabbitmq']['host'],
                port=self.conf['rabbitmq']['port'],
                credentials=pika.PlainCredentials(
                    self.conf['rabbitmq']['username'],
                    self.conf['rabbitmq']['password']
                )
            )
        )
        self.mq_channel = self.mq_conn.channel()

    def exit_handler(self, signum, frame):
        self.alive = False

    def main_loop(self):
        while self.alive:
            print(self.alive)
            # do stuff:
            print("Doing stuff ...")
            # wait interval:
            i = 0
            while i < 3:
                print(i)
                time.sleep(1)
                if not self.alive:
                    break
                i += 1


def main():
    scanner = Scanner("")
    signal.signal(signal.SIGINT, scanner.exit_handler)
    signal.signal(signal.SIGTERM, scanner.exit_handler)
    #signal.signal(signal.CTRL_C_EVENT, scanner.exit_handler)
    scanner.main_loop()


if __name__ == "__main__":
    main()
