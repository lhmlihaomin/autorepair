#!/usr/bin/python
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

from asset.models import Module, Region
###############################################################################

import MySQLdb

USER = "root"
PASS = "root"
DBNAME = "prd_deployer"

db = MySQLdb.connect(user=USER, password=PASS)
db.select_db(DBNAME)
cursor = db.cursor()
sql = """
SELECT t1.name, t1.current_version, t1.service_type, t1.configuration, t2.name 
FROM updateplanmgr_module t1, awscredentialmgr_awsregion t2 
WHERE t1.region_id = t2.id
"""
cursor.execute(sql)
result = cursor.fetchall()
for row in result:
    name = row[0]
    version = row[1]
    service_type = row[2]
    configuration = row[3]
    region_name = row[4]
    #print("%s (%s)"%(name, version))
    try:
        region = Region.objects.get(name=region_name)
    except:
        print("Region not found: "+region_name)
        continue
    try:
        module = Module.objects.get(name=name, version=version, region=region)
        print("Module already exists: "+str(module))
    except:
        module = Module()
        module.name = name
        module.version = version
        module.launch_config = configuration
        module.service_type = service_type
        module.region = region
        module.save()
        print(str(module))
