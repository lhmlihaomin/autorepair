# -*- coding: utf-8 -*-
import datetime
import pytz

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import exceptions

from asset.models import Region, Module, OnlineEvent, EC2Instance

class OnlineEventSerializer(serializers.ModelSerializer):
    """
    Serializer class for OnlineEvent model. 

    Translates region_name to region (id, FK). Other fields not changed.

    Attributes
    ---
    region_name: str
        Name of an AWS Region
    """
    # region = serializers.RelatedField(required=False)
    region_name = serializers.CharField(max_length=100)

    class Meta:
        model = OnlineEvent
        fields = ('id', 'source', 'resource_type', 'event_type', 'resource_id',
                  'detail', 'region_name')

    def create(self, vdata): # `vdata` = `validated data`
        try:
            region = Region.objects.get(name=vdata.pop('region_name'))
        except Region.DoesNotExist:
            raise exceptions.NotFound
        online_event = OnlineEvent.objects.create(**vdata)
        online_event.region = region
        online_event.save()
        return online_event


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer class for Module model."""
    # region_name = serializer_choice_field.CharField(max_length=100)
    region_name = serializers.CharField(max_length=100)

    class Meta:
        model = Module
        fields = ('id', 'name', 'version', 'launch_config', 'service_type',\
                  'region_name', 'active')

    def create(self, vdata): # `vdata` = `validated data`
        pass


class EC2InstanceSerializer(serializers.ModelSerializer):
    """Serializer class for EC2 instance."""
    class Meta:
        model = EC2Instance
        fields = ('module', 'region', 'status', 'active', 'last_update_time',\
                  'name', 'instance_id', 'username', 'private_ip_address',\
                  'key_pair')
                  