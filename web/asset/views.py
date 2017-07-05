import boto3
from django.shortcuts import render

from .models import Region, EC2Instance

# Create your views here.
def sync_instances(request):
    if request.GET.get('region'):
        regions = [
            Region.objects.get(name=request.GET.get('region')),
        ]
    else:
        regions = Region.objects.all()
    for region in regions:
        session = boto3.Session(
            profile_name=region.profile_name,
            region_name=region.name
        )
        