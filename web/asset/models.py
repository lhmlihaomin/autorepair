# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models

class Region(models.Model):
    """
    An AWS Region.

    Attributes
    ---
    name: str
        The name of the region. e.g. eu-west-1
    tag_name: str
        Region code used in EC2 instance tags. e.g. euw1
    full_name: str
        Full name of the region. e.g. Ireland
    profile_name: str
        AWS profile name associated with this region.
    """
    name = models.CharField(max_length=100)
    tag_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=500)
    profile_name = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()


class Module(models.Model):
    """
    An individual module of a certain version in one region.
    
    Attributes
    ---
    name: str
        Name of the module. e.g. account
    version: str
        Module version. e.g. "1.2.3"
    launch_config: str
        EC2 instance launch parameters in JSON format
    service_type: str
        Service type. e.g. standard|tomcat|...
    region: FK to Region
    """
    name = models.CharField(max_length=500)
    version = models.CharField(max_length=500)
    launch_config = models.TextField()
    service_type = models.CharField(max_length=500)
    region = models.ForeignKey(Region)
    active = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return "%s-%s-%s"%(self.name, self.version, self.region.tag_name)

    def __unicode__(self):
        return unicode(self.__str__())

    @property
    def region_name(self):
        return self.region.name

    @property
    def environ(self):
        if self.profile.name.endswith("alpha"):
            return "dev"
        elif self.profile.name.endswith("beta"):
            return "uat"
        elif self.profile.name.endswith("prd"):
            return "prd"
        elif self.profile.name.endswith("fast"):
            return "fprd"
        elif self.profile.name.endswith("mercury"):
            return "mprd"

    @property
    def instance_name_prefix(self):
        return "-".join([
        #self.environ,
        'dev',
        self.name,
        self.version,
        self.region.tag_name
    ])

    @property
    def current_version(self):
        return self.version


class EC2Instance(models.Model):
    """
    An EC2 instance.
    
    Attributes
    ---
    module: FK to Module
    region: FK to Region
    status: bool
        True: OK, False: down.
    active: bool
        True: in use, False: decommissioned.
    created_at: datetime
        Time when this instance is created.
    last_checked_at: datetime
        Time of last check operation on this instance.
    name: str
        `Name` tag of instance.
    instance_id: str
    username: str
    private_ip_address: str
    key_pair: str
        Name of SSH key without `.pem` extension.    
    note: str
        Additional info.
    """
    # belonging:
    module = models.ForeignKey(Module)
    region = models.ForeignKey(Region)
    # status:
    status = models.BooleanField()
    active = models.BooleanField(default=True)
    #last_update_time = models.DateTimeField()
    last_checked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(default="")
    # static information:
    name = models.CharField(max_length=500)
    instance_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)
    private_ip_address = models.CharField(max_length=500)
    key_pair = models.CharField(max_length=500)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.__str__())

    @property
    def region_name(self):
        return self.region.name


class OnlineEvent(models.Model):
    """
    An online event.

    Attributes
    ---
    source: str
    resource_type: str
    event_type: str
    resource_id: str
    event_state: str
    detail: text
    result_detail: text
    created_at: datetime, auto
    region: FK to Region

    Notes
    ---
    `event_state` workflow:
    new --> in_progress --> solved
                    (or) \--> error
    """
    source = models.CharField(max_length=500)
    resource_type = models.CharField(max_length=500)
    event_type = models.CharField(max_length=500)
    resource_id = models.CharField(max_length=500)
    event_state = models.CharField(max_length=100)
    detail = models.TextField()
    result_detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    region = models.ForeignKey(Region, default=1)

    def to_dict(self):
        return {
            'source': self.source,
            'resource_type': self.resource_type,
            'event_type': self.event_type,
            'resource_id': self.resource_id,
            'event_state': self.event_state,
            'detail': self.detail,
            'result_detail': self.result_detail,
            'create_at': datetime.datetime.strftime(
                self.created_at, "%Y-%m-%d %H:%M:%S"
            ),
            'region': self.region.name
        }

    @property
    def region_name(self):
        return self.region.name


class EventLog(models.Model):
    """
    Online event log.
    
    Attributes
    ---
    event: FK to OnlineEvent
    start_time: datetime
    end_time: datetime
    action: str
    result: str
    args: text
        Additional information about the action.
    note: text
    """
    event = models.ForeignKey(OnlineEvent)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    action = models.CharField(max_length=500)
    result = models.CharField(max_length=100)
    args = models.TextField()
    note = models.TextField()


class EventHandleRule(models.Model):
    """
    Rule of how to handle certain event types on modules.

    Attributes
    ---
    module_name: str
    event_type: str
    handler: str
        Predefined handler name.
    """
    module_name = models.CharField(max_length=500, db_index=True)
    event_type = models.CharField(max_length=500)
    handler = models.CharField(max_length=500)


class AutoRepairSwitch(models.Model):
    """Switch to enable/disable auto repair."""
    auto_repair = models.BooleanField()

    @classmethod
    def enable(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = AutoRepairSwitch(auto_repair=True)
            obj.save()
        elif not obj.auto_repair:
            obj.auto_repair = True
            obj.save()
        return True

    @classmethod
    def disable(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = AutoRepairSwitch(auto_repair=False)
            obj.save()
        elif obj.auto_repair:
            obj.auto_repair = False
            obj.save()
        return True
        

    @classmethod
    def auto_repair_enabled(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = AutoRepairSwitch(auto_repair=True)
            obj.save()
        return obj.auto_repair


class SecurityGroupIsolated(models.Model):
    """The security group with no outbound rules in each VPC."""
    vpc_id = models.CharField(max_length=200, db_index=True)
    group_name = models.CharField(max_length=200)
    group_id = models.CharField(max_length=200)
    note = models.CharField(max_length=200, default='', blank=True)

    def __str__(self):
        return "{0} - {1}".format(self.group_name, self.note)

    def __unicode__(self):
        return unicode(self.__str__())

    @staticmethod
    def get_by_vpc_id(vpc_id):
        return SecurityGroupIsolated.objects.get(vpc_id=vpc_id)
