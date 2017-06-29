"""
ec2client = session.client('ec2')
response = ec2client.describe_instance_status()
response['InstanceStatuses'][0]['Events']
# Sample events:
events = [{u'Code': 'instance-stop', u'Description': 'The instance is running on degraded hardware', u'NotBefore': datetime.datetime(2017, 7, 5, 0, 0, tzinfo=tzutc())}]
"""
import threading

import boto3

from asset.models import OnlineEvent

class EventHandler(object):
    


class InstanceStatusChecker(threading.Thread):
    """Use AWS 'describe_instance_status' and search for 'Events'."""
    def __init__(self, region, mq_lock):
        super(self, InstanceStatusChecker).__init__()
        self.region = region
        self.mq_lock = mq_lock
    
    def get_status(self):
        session = boto3.Session(
            profile_name=self.region.profile_name, 
            region_name=self.region.name
        )
        ec2client = session.client('ec2')
        response = ec2client.describe_instance_status()
        return response['InstanceStatuses']

    def get_events(self):
        statuses = self.get_status()
        self.events = []
        for status in statuses:
            if status.has_key('Events'):
                #ret.append({'instance_id': status['InstanceId'], 'event': status['Events'][0],})
                self.events.append({
                    'source': 'instance_status',
                    'resource_type': 'EC2',
                    'resource_id': status['InstanceId'],
                    'event_type': status['Events'][0]['Code'],
                    'detail': status['Events'][0]['Description'],
                })
        return self.events

    def print_events(self):
        for event in self.events:
            for key in event:
                print("%15s: %s"%(key, event[key]))

    def create_event_db(self):
        pass

    def create_event_mq(self):
        pass

    def run(self):
        self.get_events()
