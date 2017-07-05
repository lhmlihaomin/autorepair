from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'sync_ec2', views.sync_ec2),
]