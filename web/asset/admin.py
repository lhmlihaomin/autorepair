# -*- coding: utf-8 -*-
from django.contrib import admin
from asset.models import Module, SecurityGroupIsolated

# Register your models here.
admin.site.register(Module)
admin.site.register(SecurityGroupIsolated)
