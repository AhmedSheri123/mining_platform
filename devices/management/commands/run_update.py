# devices/management/commands/run_update.py
import time
from django.core.management.base import BaseCommand
from devices.models import MyDeviceModel
from decimal import Decimal, getcontext
import random
from devices.utils import get_earnings_increment 
# زيادة دقة Decimal
from datetime import date
from accounts.models import DailyEarning

class Command(BaseCommand):
    help = "Run update_devices_task every second (for testing on Windows)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting update_devices_task loop..."))
        while True:
            devices = MyDeviceModel.objects.filter(status='running')
            for device in devices:

                # تحديث القيم العشوائية بنسبة ±5%
                device.hashrate = random.randint(
                    int(device.hashrate), int(device.hashrate + device.hashrate * 0.05)
                )
                device.temperature = random.randint(
                    int(device.temperature), int(device.temperature + device.temperature * 0.05)
                )
                device.wattage = random.randint(
                    int(device.wattage), int(device.wattage + device.wattage * 0.05)
                )

                # تشغيل المرحلة الحالية واستهلاك الطاقة
                result = device.run_stage()

                if 'error' in result:
                    print(f"[WARN] {device} could not run stage: {result['error']}")
                else:
                    print(f"[INFO] {device} stage {result['stage']} profit: {result['profit']} energy left: {result['energy_left']}")

            time.sleep(1)  # تحديث كل ثانية
