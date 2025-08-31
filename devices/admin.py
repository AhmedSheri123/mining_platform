from django.contrib import admin
from .models import DeviceModel, MyDeviceModel, DeviceStagesModel
# Register your models here.
admin.site.register(DeviceModel)
admin.site.register(MyDeviceModel)
admin.site.register(DeviceStagesModel)