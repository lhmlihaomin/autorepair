import json
import re

import boto3


def run_instances(ec2res, module, count):
    """Run 'count' number of instances use settings defined in 'module'.
    Returns a list of instance ids on success.
    """
    opset = json.loads(module.launch_config)
    # check disk settings:
    block_device_mappings = []
    #if not opset['use_default_ebs_settings'] and opset['volume_type'] == 'io1':
    if not opset['use_default_ebs_settings']:
        bdm = {
            #'VirtualName': '',
            'DeviceName': '/dev/sda1',
            'Ebs': {
                #'SnapshotId': '',
                'VolumeSize': opset['volume_size'],
                'DeleteOnTermination': True,
                'VolumeType': opset['volume_type'],
                'Iops': opset['volume_iops'],
                #'Encrypted': False
            },
            #'NoDevice': ''
        }
        # boto3 can't just fucking ignore Iops if volume_type is not io1:
        if opset['volume_type'] != 'io1':
            del bdm['Ebs']['Iops']
        block_device_mappings = [bdm]
    # check security group settings:
    if opset.has_key('security_group_names'):
        security_group_ids = get_security_group_ids_by_name(
            ec2res,
            opset['vpc'][1],
            opset['security_group_names']
        )
    elif opset.has_key('security_groups'):
        security_group_ids = [x[1] for x in opset['security_groups']]
    else:
        security_group_ids = [opset['security_group'][1]]
    # try to run instances:
    try:
        instances = ec2res.create_instances(
            BlockDeviceMappings=block_device_mappings,
            IamInstanceProfile={
                'Arn': opset['instance_profile'][1]
            },
            ImageId=opset['image'][1],
            InstanceType=opset['instance_type'],
            KeyName=opset['keypair'][1],
            MinCount=count,
            MaxCount=count,
            SecurityGroupIds=security_group_ids,
            # TODO: handle insufficient IP address error:
            SubnetId=opset['subnets'][0][1],
        )
        return instances
        #instance_ids = [x.id for x in instances]
        #return instance_ids
    except Exception as ex:
        raise ex

def find_name_tag(instance):
    for tagpair in instance.tags:
        if tagpair['Key'].lower() == 'name':
            return tagpair['Value']
    return ""

def add_instance_tags(ec2res, module, instance_ids):
    def get_instances_max_number(prefix, instances):
        p = prefix+"-[a-zA-Z]+-(\d+)"
        max_number = -1
        for instance in instances:
            n = find_name_tag(instance)
            m = re.match(p, n)
            if m is not None:
                num = int(m.groups()[0])
                if num > max_number:
                    max_number = num
        return max_number

    '''if len(instance_ids) > optionset.instance_count:
        raise Exception("More instance id than module.instance_count.")'''

    ret = {}
    prefix = module.instance_name_prefix
    # list instances with the same prefix:
    instances = ec2res.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [prefix+"*"]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped', 'stopping', 'pending']
            }
        ]
    )
    # get largest instance number:
    max = get_instances_max_number(prefix, instances)
    # tag each instance:
    tags = json.loads(module.launch_config)['tags']
    num = max + 1
    instances = ec2res.instances.filter(InstanceIds=instance_ids)
    for instance in instances:
        instance_id = instance.id
        az = instance.subnet.availability_zone[-1]
        instance_name = "%s-%s-%03d"%(prefix, az, num)
        tags.update({'Name': instance_name})
        boto3tags = []
        for key in tags.keys():
            boto3tags.append({
                'Key': key,
                'Value': tags[key]
            })
        num += 1

        try:
            #instance = ec2res.Instance(instance_id)
            instance.create_tags(
                Tags=boto3tags
            )
            ret.update({instance_id: instance_name})
        except:
            ret.update({instance_id: False})
    return ret


def add_volume_tags(ec2res, instance_ids):
    """Add volume tags with instance information"""
    ret = {}
    # for each instance
    for instance_id in instance_ids:
        try:
            instance = ec2res.Instance(instance_id)
            # get volume tags:
            boto3tags = [{
                'Key': 'InstanceId',
                'Value': instance.id
            },
            {
                'Key': 'Name',
                'Value': find_name_tag(instance)
            }]
            # add tags to volume:
            #flag = True
            for volume in instance.volumes.all():
                volume.create_tags(Tags=boto3tags)
                #flag = False
            #if flag:
                # retry...
            ret.update({instance.id: True})
        except Exception as ex:
            ret.update({instance.id: False})
    return ret


def get_instances_for_ec2launchoptionset(ec2res, optionset):
    def name_cmp(x, y):
        """Compare instance names.

        For modules with +10 instances, string length needs to be considered,
        otherwise 'xxx-9' will be greater than 'xxx-10'."""
        len_x = len(x)
        len_y = len(y)
        if len_x < len_y:
            return -1
        if len_x > len_y:
            return 1
        if x < y:
            return -1
        if x > y:
            return 1
        return 0

    ret = []
    prefix = optionset.instance_name_prefix
    # list instances with the same prefix:
    instances = ec2res.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [prefix+"*"]
            },
        ]
    )

    p = prefix+"-(\d+)"
    for instance in instances:
        n = find_name_tag(instance)
        m = re.match(p, n)
        if m is not None:
            ret.append({
                'id': instance.id,
                'name': n,
                'state': instance.state['Name']
            })
            #ret.append(instance)
        ret.sort(cmp=name_cmp, key=lambda l:l['name'])
    return ret


def get_security_group_ids_by_name(ec2res, vpc_id, names):
    """Find security groups with the given names and return their ids.

    AWS does not allow the use of security group names outside the default VPC
    when launching EC2 instances. So group names must be converted to ids
    before calling run_instances."""
    filter_vpc = {
        'Name': 'vpc-id',
        'Values': [vpc_id]
    }
    filter_group_name = {
        'Name': 'group-name',
        'Values': names
    }
    group_ids = []
    for sg in ec2res.security_groups.filter(Filters=[
        filter_vpc,
        filter_group_name
    ]):
        group_ids.append(sg.id)
    return group_ids
