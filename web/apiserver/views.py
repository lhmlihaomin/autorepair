# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import datetime
import pytz
import json
import copy
import logging

import boto3
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import exceptions
# REST class views:
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import mixins
# REST function views:
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from asset.models import Region, EC2Instance, Module, OnlineEvent, EventLog,\
    EventHandleRule, AutoRepairSwitch
from apiserver.serializers import OnlineEventSerializer, ModuleSerializer,\
    EC2InstanceSerializer
from lib_msg_q import get_mq_connection


def get_instance_name(instance):
    """Retrieve `Name` tag from object."""
    for tag in instance.tags:
        if tag['Key'].lower() == 'name':
            return tag['Value']
    raise Exception(instance.id + ": Name tag not found.")


def get_instance_module(instance):
    """Get module info by parsing instance name."""
    p = r"[a-z]+-([a-zA-Z0-9]+)-([a-zA-Z0-9.]+)-([0-9a-z]+)-[a-z]{1}-[0-9]+"
    name = get_instance_name(instance)
    match = re.match(p, name)
    if match is None:
        raise Exception(name + ": Cannot parse instance name.")
    else:
        module_name, module_version, region_tag = match.groups()
        region = Region.objects.get(tag_name=region_tag)
        module = Module.objects.get(
            name=module_name,
            version=module_version,
            region=region,
            active=True
        )
        return module


def read_instances(region, instance_ids):
    """Use boto3 to get instance info from AWS API."""
    # remove existing instances:
    new_instance_ids = []
    for instance_id in instance_ids:
        if not EC2Instance.objects.filter(instance_id=instance_id).exists():
            new_instance_ids.append(instance_id)
    if len(new_instance_ids) == 0:
        return None
    # AWS API read:
    session = boto3.Session(
        profile_name=region.profile_name,
        region_name=region.name
    )
    resource = session.resource('ec2')
    ret = []
    many_data = []
    for instance in resource.instances.filter(InstanceIds=new_instance_ids):
        try:
            module = get_instance_module(instance)
        except Module.DoesNotExist:
            raise exceptions.NotFound

        tz = pytz.timezone(settings.TIME_ZONE)
        now = tz.localize(datetime.datetime.now())
        many_data.append({
            'module': module.id,
            'region': module.region.id,
            'status': True,
            'active': True,
            'created_at': now,
            'name': get_instance_name(instance),
            'instance_id': instance.id,
            'username': 'ubuntu',
            'private_ip_address': instance.private_ip_address,
            'key_pair': instance.key_pair.name
        })
    serializers = EC2InstanceSerializer(data=many_data, many=True)
    return serializers


class OnlineEventCreation(generics.CreateAPIView):
    queryset = OnlineEvent.objects.all()
    serializer_class = OnlineEventSerializer
    

class OnlineEventCreationMixin(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = OnlineEvent.objects.all()
    serializer_class = OnlineEventSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = copy.copy(serializer.validated_data)
            region = Region.objects.get(name=data.pop('region_name'))
            data.update({'region': region})
            event = OnlineEvent(**data)
            event.save()
            # publish to message queue:
            mq_conn, mq_channel = get_mq_connection(settings.MQ_CONF, 'apiserver')
            mq_channel.basic_publish(
                'topic_events',
                'events.ec2.'+event.event_type,
                json.dumps({'event_id': event.id})
            )
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleView(APIView):
    def put(self, request, *args, **kwargs):
        region_name = kwargs.get('region_name')
        module_name = kwargs.get('module_name')
        version = kwargs.get('version')
        try:
            region = Region.objects.get(name=region_name)
        except Region.DoesNotExist:
            raise exceptions.NotFound()
        try:
            module = Module.objects.get(
                region=region,
                name=module_name,
                version=version
            )
            print("Module already exists.")
        except Module.DoesNotExist:
            print request.data.get('launch_config')
            print request.data.get('service_type')
            module = Module(
                name=module_name,
                version=version,
                launch_config=request.data.get('launch_config'),
                service_type=request.data.get('service_type'),
                region=region
            )
            module.save()
            print(module)
        return Response({'method': 'PUT'})

    def get(self, request, *args, **kwargs):
        region_name = kwargs.get('region_name')
        module_name = kwargs.get('module_name')
        version = kwargs.get('version')
        try:
            region = Region.objects.get(name=region_name)
        except Region.DoesNotExist:
            raise exceptions.NotFound()
        try:
            module = Module.objects.get(
                region=region,
                name=module_name,
                version=version
            )
            serializer = ModuleSerializer(module)
            return Response(serializer.data)
        except Module.DoesNotExist:
            raise exceptions.NotFound

    def patch(self, request, *args, **kwargs):
        return Response({'method': 'PATCH'})


@api_view(['POST'])
def create_ec2_instances(request):
    try:
        region = Region.objects.get(name=request.data.get('region'))
        instance_ids = request.data.get('instance_ids')
    except:
        return Response([], status=status.HTTP_400_BAD_REQUEST)
    serializer = read_instances(region, instance_ids)
    if serializer is None:
        return Response(status=status.HTTP_200_OK)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def deactivate_ec2_instances(request):
    try:
        region = Region.objects.get(name=request.data.get('region'))
        instance_ids = request.data.get('instance_ids')
    except:
        return Response("", status=status.HTTP_400_BAD_REQUEST)
    serializers = []
    for instance_id in instance_ids:
        try:
            serializers.append(EC2InstanceSerializer(
                EC2Instance.objects.get(instance_id=instance_id),
                data={'active': False},
                partial=True
            ))
        except EC2Instance.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    for serializer in serializers:
        if serializer.is_valid():
            serializer.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def pause_auto_repair(request):
    try:
        reason = request.data.get('reason')
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if reason is None:
        return Response("Reason cannot be None.", status=status.HTTP_400_BAD_REQUEST)
    AutoRepairSwitch.disable()
    return Response("", status=status.HTTP_200_OK)


@api_view(['POST'])
def resume_auto_repair(request):
    try:
        reason = request.data.get('reason')
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    AutoRepairSwitch.enable()
    return Response("", status=status.HTTP_200_OK)
