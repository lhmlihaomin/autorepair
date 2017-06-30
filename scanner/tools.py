import boto3
import re

PATTERN = r"([adehlprtu]+)-([a-zA-Z0-9_]+)-([0-9._]+)-([a-z0-9]+)-([a-z]+)-(\d+)"
#            ENVRION        MODULE          VER       REGION      AZ       NUM

def find_name_tag(tags):
    for tag in tags:
        if tag['Key'].lower() == 'name':
            return tag['Value']
    return ""

modules = {}

session = boto3.Session(profile_name='cn-beta', region_name='cn-north-1')
resource = session.resource('ec2')
for instance in resource.instances.filter():
    name = find_name_tag(instance.tags)
    try:
        groups = re.match(PATTERN, name).groups()
        envion, module_name, module_version, region_code, az, num = groups
        if not modules.has_key(module_name+"-"+module_version):
            modules.update({
                module_name+"-"+module_version: (module_name, module_version)
            })
    except:
        pass

for key in modules.keys():
    print("%s (%s)"%(modules[key][0], modules[key][1]))
