from django.conf.urls import url
from asset import views

urlpatterns = [
    url(r'sync_ec2', views.sync_ec2),
    url(r'api/$', views.OnlineEventList.as_view()),
    url(r'api/(?P<pk>[0-9]+)/$', views.OnlineEventDetail.as_view()),
    url(r'api/create_event/$', views.xxx),
    #url(r'api/modules/(?P<region_name>.+)/(?P<module_name>.+)/(?P<version>.+)/$', views.xxx),
    ## Use the same url for PATCH: url(r'api/modules/(?P<region_name>.+)/(?P<module_name>.+)/(?P<version>.+)/$', views.xxx),
    #url(r'api/create_ec2_instances/$', views.xxx),
    #url(r'api/deactivate_ec2_instances/$', views.xxx),
    #url(r'api/pause_auto_repair/$', views.xxx),
    #url(r'api/resume_auto_repair/$', views.xxx),
]
