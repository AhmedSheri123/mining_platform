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
                # تحديث القيم العشوائية
                device.hashrate = random.randint(device.device.hashrate_from, device.device.hashrate_to)
                device.temperature = random.randint(device.device.temperature_from, device.device.temperature_to)

                # حساب زيادة الأرباح المضمونة
                earnings_increment = get_earnings_increment(
                                            device.device.daily_profit_from,
                                            device.device.daily_profit_to
                                        )


                # إضافة الأرباح وحفظها
                device.earnings += earnings_increment
                device.owner.profile.balance += earnings_increment
                device.owner.profile.total_earned += earnings_increment

                today = date.today()
                daily_record, created = DailyEarning.objects.get_or_create(user=device.owner, date=today)
                daily_record.earned += earnings_increment
                daily_record.save()

                device.save()
                device.owner.profile.save()
                print(f"[INFO] {device} earnings updated: {device.earnings}")

            print(f"[INFO] update_devices_task executed, updated {devices.count()} devices")
            time.sleep(1)  # الانتظار ثانية واحدة قبل التكرار
