from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Region(models.Model):
    """An AWS region"""
    name = models.CharField(max_length=100)
    tag_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=500)
    profile_name = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()


class Module(models.Model):
    """An individual module of a certain version in one region"""
    name = models.CharField(max_length=500)
    version = models.CharField(max_length=500)
    launch_config = models.TextField()
    service_type = models.CharField(max_length=500)
    region = models.ForeignKey(Region)

    def __str__(self):
        return "%s-%s-%s"%(self.name, self.version, self.region.tag_name)

    def __unicode__(self):
        return unicode(self.__str__())


class EC2Instance(models.Model):
    """An EC2 instance"""
    # belonging:
    module = models.ForeignKey(Module)
    region = models.ForeignKey(Region)
    # status:
    status = models.BooleanField()
    active = models.BooleanField(default=True)
    last_update_time = models.DateTimeField()
    # static information:
    name = models.CharField(max_length=500)
    instance_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)
    private_ip_address = models.CharField(max_length=500)
    key_pair = models.CharField(max_length=500)


class ELB(models.Model):
    """An Elastic Load Balancer"""
    # belonging:
    module = models.ForeignKey(Module)
    region = models.ForeignKey(Region)
    # status:
    status = models.BooleanField()
    active = models.BooleanField(default=True)
    last_update_time = models.DateTimeField()
    # static_information:
    name = models.CharField(max_length=500)
    dns_name = models.CharField(max_length=500)
    scheme = models.CharField(max_length=100)


class OnlineEvent(models.Model):
    """An online event"""
    source = models.CharField(max_length=500)
    resource_type = models.CharField(max_length=500)
    event_type = models.CharField(max_length=500)
    resource_id = models.CharField(max_length=500)
    event_state = models.CharField(max_length=100)
    detail = models.TextField()
    result_detail = models.TextField()


class EventLog(models.Model):
    """Online event log"""
    event = models.ForeignKey(OnlineEvent)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    action = models.CharField(max_length=500)
    result = models.CharField(max_length=100)
    args = models.TextField()
    note = models.TextField()


class EventHandleRule(models.Model):
    module_name = models.CharField(max_length=500, db_index=True)
    event_type = models.CharField(max_length=500)
    handler = models.CharField(max_length=500)
