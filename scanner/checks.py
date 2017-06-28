"""
ec2client = session.client('ec2')
response = ec2client.describe_instance_status()
response['InstanceStatuses'][0]['Events']
# Sample events:
events = [{u'Code': 'instance-stop', u'Description': 'The instance is running on degraded hardware', u'NotBefore': datetime.datetime(2017, 7, 5, 0, 0, tzinfo=tzutc())}]
"""
import boto3

def get_status(region):
    session = boto3.Session(profile_name=region.profile_name, region_name=region.name)
    ec2client = session.client('ec2')
    response = ec2client.describe_instance_status()
    return response['InstanceStatuses']


def get_events(region):
    statuses = get_status(region)
    ret = []
    for status in statuses:
        if status.has_key('Events'):
            ret.append({'instance_id': status['InstanceId'], 'event': status['Events'][0],})
    return ret


def print_events(events):
    for event in events:
        print("Instance id: "+event['instance_id']+": ")
        print("Event: "+event['event']['Code'])
        print('Description: '+event['event']['Description'])
        print("")
