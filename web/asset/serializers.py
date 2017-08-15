from rest_framework import serializers
from rest_framework import exceptions

from asset.models import Region, OnlineEvent


class OnlineEventSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(max_length=100)

    class Meta:
        model = OnlineEvent
        fields = ('id', 'source', 'resource_type', 'event_type', 'resource_id',
                  'detail', 'region_name')

    def create(self, vdata): # `vdata` for `validated data`
        print vdata.keys()
        try:
            region = Region.objects.get(name=vdata.pop('region_name'))
        except Region.DoesNotExist:
            raise exceptions.NotFound
        online_event = OnlineEvent.objects.create(**vdata)
        online_event.region = region
        online_event.save()
        return online_event
