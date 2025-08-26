from django.contrib import admin
from .models import DeviceModel, MyDeviceModel
# Register your models here.
admin.site.register(DeviceModel)
admin.site.register(MyDeviceModel)