#!/usr/bin/python

import MySQLdb

DB_FROM = 'prd_deployer'
USER_FROM = 'prd_deployer'
PASS_FROM = 'tplinkcloud'
TABLE_FROM = 'updateplanmgr_module'

DB_TO = 'autorepair'
USER_TO = 'autorepair'
PASS_TO = 'autorepair'
TABLE_TO = 'asset_module'

conn_from = MySQLdb.connect('127.0.0.1', USER_FROM, PASS_FROM)
conn_from.select_db(DB_FROM)
cursor_from = conn_from.cursor(MySQLdb.cursors.DictCursor)

conn_to = MySQLdb.connect('127.0.0.1', USER_TO, PASS_TO)
conn_to.select_db(DB_TO)
cursor_to = conn_to.cursor(MySQLdb.cursors.DictCursor)

# Read modules from prd_deployer database:
sql = """
SELECT 
    `t1`.`name`, 
    `t1`.`current_version`, 
    `t1`.`configuration`, 
    `t1`.`service_type`, 
    `t2`.`name` AS `region_name`,
    `t2`.`tag_name` AS `region_tag`
FROM 
    `updateplanmgr_module` `t1`, 
    `awscredentialmgr_awsregion` `t2`
WHERE 
    #`t1`.`is_online_version`=1
    #AND 
    `t1`.`region_id` = `t2`.`id`
"""
cursor_from.execute(sql)
rows = cursor_from.fetchall()

# Convert fields:
sql = """
SELECT `id`, `name` FROM `asset_region`
"""
cursor_to.execute(sql)
regions = {}
for row in cursor_to.fetchall():
    regions.update({row['name']: row['id']})

# Write modules to autorepair database:
sql_fmt = """
INSERT INTO `asset_module` VALUES (
    0,
    '{name}',
    '{version}',
    '{launch_config}',
    '{service_type}',
    '{region_id}',
    1
);
"""
with open('dep2rep.sql', 'w') as fp:
    for row in rows:
        print row['name']+"-"+row['current_version']
        sql = sql_fmt.format(
            name=row['name'],
            version=row['current_version'],
            launch_config=row['configuration'],
            service_type=row['service_type'],
            region_id=regions[row['region_name']]
        )
        fp.write(sql)
        fp.write('####################\n')
        print '####################'
