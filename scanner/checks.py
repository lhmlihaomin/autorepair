
ec2client = session.client('ec2')
response = ec2client.describe_instance_status()
response['InstanceStatuses'][0]['Events']
# Sample events:
events = [{u'Code': 'instance-stop', u'Description': 'The instance is running on degraded hardware', u'NotBefore': datetime.datetime(2017, 7, 5, 0, 0, tzinfo=tzutc())}]
