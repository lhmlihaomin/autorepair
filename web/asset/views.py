import re
import datetime

from django.http import HttpResponse
from django.shortcuts import render
import boto3
import pytz

from .models import Region, EC2Instance, Module


def get_resource_name(resource):
    for tag in resource.tags:
        if tag['Key'].lower() == 'name':
            return tag['Value']
    return None


def sync_ec2(request):
    NAME_PATTERN = "[adeprtuv]+-([a-zA-Z0-9_]+)-([0-9._]+)-([a-z0-9]+)-([a-z]{1})-([0-9]+)"
    #               ENV  MODULE_NAME     VERSION    REGION      AZ         NUM
    output = ""
    # get regions
    if request.GET.get('region'):
        regions = [Region.objects.get(name=request.GET.get('region')),]
    else:
        regions = Region.objects.all()
    for region in regions:
        # init boto3 resource:
        session = boto3.Session(
            profile_name=region.profile_name,
            region_name=region.name
        )
        resource = session.resource('ec2')
        for instance in resource.instances.filter(
            Filters=[
                {
                    'Name': 'instance-state-name', 
                    'Values': [
                        'running',
                    ]
                }
            ]
        ):
            # get instance id & name:
            instance_id = instance.id
            instance_name = get_resource_name(instance)
            if instance_name is None:
                output += "Instance name not found: %s\r\n<br/>"%(instance_id,)
                continue
            # check if instance id exists:
            num = EC2Instance\
                  .objects\
                  .filter(instance_id=instance_id)\
                  .count()
            if num > 0:
                output += "Instance already exists: %s (%s)\r\n<br/>"%(
                    instance_id, 
                    instance_name
                )
                continue
            # parse instance name, find out module name & version:
            match = re.match(NAME_PATTERN, instance_name)
            if match is None:
                output += "Naming error for: %s (%s)\r\n<br/>"%(
                    instance_id, 
                    instance_name
                )
                continue
            module_name = match.groups()[0]
            module_version = match.groups()[1]
            # check if module exists:
            try:
                module = Module.objects.get(
                    name=module_name,
                    version=module_version,
                    region=region
                )
            except:
                output += "Module not found for: %s (%s)\r\n<br/>"%(
                    instance_id, 
                    instance_name
                )
                continue
            # create EC2Instance
            output += "CREATING INSTANCE: %s (%s)\r\n<br/>"%(
                instance_id,
                instance_name
            )
            tz = pytz.timezone(u"Asia/Chongqing")
            now = tz.localize(datetime.datetime.now())
            ec2instance = EC2Instance(
                status=True,
                active=True,
                last_update_time=now,
                name=instance_name,
                instance_id=instance_id,
                username='ubuntu',
                private_ip_address=instance.private_ip_address,
                key_pair=instance.key_pair.name,
                module=module,
                region=region
            )
            ec2instance.save()

    return HttpResponse(output)
