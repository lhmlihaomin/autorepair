from django.contrib import admin
from .models import Region, Module, EC2Instance, ELB, OnlineEvent, EventLog, \
EventHandleRule

# Register your models here.
admin.site.register(Region)
admin.site.register(Module)
admin.site.register(EC2Instance)
admin.site.register(ELB)
admin.site.register(OnlineEvent)
admin.site.register(EventLog)
admin.site.register(EventHandleRule)
