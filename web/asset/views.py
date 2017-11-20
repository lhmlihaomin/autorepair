# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from asset.models import OnlineEvent, EC2Instance, EventLog


regular_decorators = [login_required]


class IndexView(View):
    template_name = 'asset/index.html'
    context = {
        'title': "Home"
    }

    @method_decorator(login_required)
    def get(self, request):
        return render(request, self.template_name, self.context)
    

class HostsView(View):
    template_name = 'asset/hosts.html'
    context = {
        'title': "Hosts"
    }

    @method_decorator(login_required)
    def get(self, request):
        hosts = EC2Instance.objects.all()
        if request.GET.get('region_name'):
            hosts = hosts.filter(region__name=request.GET.get('region_name'))
        self.context['hosts'] = hosts
        return render(request, self.template_name, self.context)


class OnlineEventsView(View):
    template_name = 'asset/online_events.html'
    context = {
        'title': "Online Events"
    }

    @method_decorator(login_required)
    def get(self, request):
        events = OnlineEvent.objects.all()
        filters = {}
        if request.GET.get('region_name'):
            events = events.filter(region__name=request.GET.get('region_name'))
            filters['region_name'] = request.GET.get('region_name')
        if request.GET.get('event_state'):
            events = events.filter(event_state=request.GET.get('event_state'))
            filters['event_state'] = request.GET.get('event_state')
        if request.GET.get('resource_type'):
            events = events.filter(resource_type=request.GET.get('resource_type'))
            filters['resource_type'] = request.GET.get('resource_type')
        print(filters)
        self.context['events'] = events
        self.context['filters'] = filters
        return render(request, self.template_name, self.context)


class EventLogsView(View):
    template_name = 'asset/event_logs.html'
    context = {
        'title': "Event Logs"
    }

    def get(self, request):
        self.context['event_logs'] = EventLog.objects.all()
        return render(request, self.template_name, self.context)



class EC2InstanceView():
    pass
