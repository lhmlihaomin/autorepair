#!/usr/bin/python
"""
Scanner module searches for abnormal events about online resources.
If an event is detected, it is then pushed into the MQ for judge module to 
analyse.
"""

import boto3
import pika

# Init:
## Read configurations:

## Connect to MQ and DB:

## Spawn thread for each type of check:
