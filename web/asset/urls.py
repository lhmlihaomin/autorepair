from django.conf.urls import url
from asset import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'online_events/$', views.OnlineEventsView.as_view(), name='online_events'),
    url(r'hosts/$', views.HostsView.as_view(), name='hosts'),
    url(r'event_logs/$', views.EventLogsView.as_view(), name='event_logs'),
]
