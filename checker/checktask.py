#!/usr/bin/python
"""
Perform background check actions. Check if EC2 instances are ready.

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
print parent_path
print django_path
sys.path.append(parent_path)
sys.path.append(django_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'
django.setup()

from django.conf import settings
###############################################################################

from asset.models import Module, EC2Instance
from ec2checker import EC2Checker, CheckRunner

runners = []
# Read instance and module:
for instance in EC2Instance.objects.filter(status=False, active=True):
    module = instance.module
    # 
    checker = EC2Checker(
        module,
        instance,
        settings.PEM_DIR,
        settings.TIME_ZONE,
        300
    )
    runner = CheckRunner(checker)
    runners.append(runner)

# Start runners:
for runner in runners:
    runner.start()

for runner in runners:
    runner.join()
