from django.urls import path
from . import views

urlpatterns = [
    path("devices/", views.devices, name="devices"),
    path("my-devices/", views.my_devices, name="my_devices"),
    path('status/', views.devices_status, name='devices_status'),
    path("device/<int:pk>/", views.device_detail, name="device_detail"),
    path("buy-device/<int:pk>/", views.buy_device, name="buy_device"),
]