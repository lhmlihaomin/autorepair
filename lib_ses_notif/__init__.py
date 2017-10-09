"""
Initialize SES service for email sending.

Author: lihaomin@tp-link.com.cn
Copyright (C), 2017, TP-LINK Technologies Co., Ltd.
"""
__version__ = "0.0.1"

import boto3


def read_conf_file(conf_file):
    with open(conf_file_path, 'r') as conffile:
        conf = json.loads(conffile.read())
    return conf


def init_ses(conf_file):
    """
    Initialize SES connection.
    Params:
        conf_file: configuration file path;
    Return:
        SES client.
    """
    conf = read_conf_file(conf_file)

    session = boto3.Session(
        profile_name=conf['profile_name'], 
        region_name=conf['region_name']
    )
    ses_client = session.client('ses')
    return ses_client
