from django.urls import path
from . import views

urlpatterns = [
    path("devices/", views.devices, name="devices"),
    path("my-devices/", views.my_devices, name="my_devices"),
    path('status/', views.devices_status, name='devices_status'),
    path("device/<int:pk>/", views.device_detail, name="device_detail"),
    path("buy-device/<int:pk>/", views.buy_device, name="buy_device"),
    path("detail/<int:device_id>/", views.stage_data, name="stage_data"),
    path("next_stage/<int:device_id>/", views.next_stage, name="next_stage"),
    path('device/<int:device_id>/next-stage/', views.next_stage_detail_ajax, name='next_stage_detail_ajax'),

]