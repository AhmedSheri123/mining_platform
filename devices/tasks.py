from celery import shared_task
from devices.models import MyDeviceModel

@shared_task
def update_device_earnings():
    devices = MyDeviceModel.objects.filter(status='running')
    for device in devices:
        try:
            # تشغيل المرحلة (تحسب الأرباح + تستهلك الطاقة إلخ...)
            result = device.run_stage()

            # ممكن ترجّع مثلاً dict من run_stage:
            # { "earnings": x, "consumption": y, "status": "done/running" }
            print(f"[INFO] Device {device.id} updated: {result}")

        except Exception as e:
            print(f"[ERROR] Failed updating device {device.id}: {e}")
