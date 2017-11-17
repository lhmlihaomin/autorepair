# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View

from asset.models import OnlineEvent


def test(request):
    return render(request, 'asset/test.html')


class OnlineEventsView(View):
    template_name = 'asset/online_events.html'
    context = {
        'title': "Online Events"
    }

    def get(self, request):
        events = OnlineEvent.objects.all()
        self.context.update({
            'events': events
        })
        return render(request, self.template_name, self.context)


class EventLogView():
    pass


class EC2InstanceView():
    pass
