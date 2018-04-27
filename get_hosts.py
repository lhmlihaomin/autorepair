#!/usr/bin/python
import boto3
import re
import MySQLdb
import datetime

PROFILE_NAME = 'cn-prd'
REGION_NAME = 'cn-north-1'
REGION_ID = 4
DB_HOST = "127.0.0.1"
DB_NAME = "autorepair"
DB_USER = "autorepair"
DB_PASS = "autorepair"
# instance name regex: "prd-(module)-(version)-(region)-(az)-(num)"
# NAMEREGEX = "prd-(module)-(version)-(region)-(az)-(num)"
NAMEREGEX = "prd-([a-zA-Z0-9]+)-([0-9.]+)-.+"

def get_name_tag(instance):
    for tag in instance.tags:
        if tag['Key'].lower() == 'name':
            return tag['Value']
    raise Exception("No name tag found.")

def instance_exists(cursor, name):
    sql = "SELECT COUNT(`id`) FROM `asset_ec2instance` WHERE `name`='{0}'".format(name)
    cursor.execute(sql)
    count = cursor.fetchone()['COUNT(`id`)']
    return count > 0

def find_instance_module(cursor, module_name, version):
    sql_fmt = "SELECT * FROM `asset_module` WHERE `name`='{name}' AND `version`='{version}'"
    sql = sql_fmt.format(name=module_name, version=version)
    cursor.execute(sql)
    rows = cursor.fetchall()
    if len(rows) < 1:
        raise Exception("Module not found: {0}-{1}".format(module_name, version))
    if len(rows) > 1:
        raise Exception("Found multiple modules with the same name & version: {0}-{1}".format(module_name, version))
    return rows[0]

def add_instance(cursor, name, instance, module_id, region_id):
    sql_fmt = """
INSERT INTO `asset_ec2instance` VALUES (
    0,
    1,
    1,
    '{name}',
    '{instance_id}',
    'ubuntu',
    '{private_ip_address}',
    '{key_pair}',
    '{module_id}',
    '{region_id}',
    '{now}',
    NULL,
    ''
);
"""
    now = datetime.datetime.now()
    sql = sql_fmt.format(
        name=name,
        instance_id=instance.id,
        private_ip_address=instance.private_ip_address,
        key_pair=instance.key_pair.name,
        module_id=module_id,
        region_id=REGION_ID,
        now=now.strftime("%Y-%m-%d %H:%M:%S")
    )
    return sql

session = boto3.Session(profile_name=PROFILE_NAME, region_name=REGION_NAME)
ec2res = session.resource('ec2')
db_conn = MySQLdb.connect(DB_HOST, DB_USER, DB_PASS)
db_conn.select_db(DB_NAME)
cursor = db_conn.cursor(MySQLdb.cursors.DictCursor)

filters = [
    {
        'Name': 'tag:Category',
        'Values': ['prd',]
    },
    {
        'Name': 'instance-state-name',
        'Values': ['running',]
    }
]

fp = open('get_hosts.sql', 'w')
for instance in ec2res.instances.filter(Filters=filters):
    # Try to get name tag:
    try:
        name = get_name_tag(instance)
    except:
        print "Name not found for " + instance.id
        continue
    # check if instance is already there:
    if instance_exists(cursor, name):
        continue

    match = re.match(NAMEREGEX, name)
    # Parse instance name for module and version:
    if match is not None:
        g = match.groups()
        module_name = g[0]
        version = g[1]
    else:
        continue
    # Try to find instance module: 
    try:
        module = find_instance_module(cursor, module_name, version)
    except Exception as ex:
        print ex
        continue
    sql = add_instance(cursor, name, instance, module['id'], REGION_ID)
    fp.write(sql)

fp.close()
