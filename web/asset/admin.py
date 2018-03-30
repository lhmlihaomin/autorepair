# -*- coding: utf-8 -*-
from django.contrib import admin
from asset.models import Region, Module, SecurityGroupIsolated, EC2Instance

# Register your models here.
admin.site.register(Region)
admin.site.register(Module)
admin.site.register(SecurityGroupIsolated)
admin.site.register(EC2Instance)
