# -*- coding: utf-8 -*-
from django.conf.urls import url
from apiserver import views

urlpatterns = [
    url(r'^create_event/$', views.OnlineEventCreationMixin.as_view()),
    url(r'modules/(?P<region_name>.+)/(?P<module_name>.+)/(?P<version>.+)/$',
        views.ModuleView.as_view()),
    url(r'create_ec2_instances/', views.create_ec2_instances),
    url(r'deactivate_ec2_instances/', views.deactivate_ec2_instances),
    url(r'pause_auto_repair/', views.pause_auto_repair),
    url(r'resume_auto_repair/', views.resume_auto_repair),
    #url(r'mv/$', views.ModuleView.as_view()),
]
