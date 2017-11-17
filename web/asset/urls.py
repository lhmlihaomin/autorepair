from django.conf.urls import url
from asset import views

urlpatterns = [
    url(r'test/$', views.test),

    url(r'online_events/$', views.OnlineEventsView.as_view()),
]
