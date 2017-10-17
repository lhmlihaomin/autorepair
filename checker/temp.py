import os
import sys
sys.path.append(os.getcwd())
from ec2checker import EC2Checker, CheckRunner
from asset.models import Module, EC2Instance

instance = EC2Instance.objects.get(pk=2)
module = Module.objects.get(pk=2)

checker = EC2Checker(module, instance, '/home/ubuntu/pem', 'Asia/Chongqing', 300)
runner = CheckRunner(checker)

