from celery import shared_task
from devices.models import MyDeviceModel
from devices.utils import get_earnings_increment
from decimal import Decimal
from datetime import date
from accounts.models import DailyEarning
import random

@shared_task
def update_device_earnings():
    devices = MyDeviceModel.objects.filter(status='running')
    for device in devices:

        device.hashrate = round(random.uniform(device.device.hashrate_from, device.device.hashrate_to), 2)
        device.temperature = round(random.uniform(device.device.temperature_from, device.device.temperature_to), 1)


        earnings_increment = get_earnings_increment(
            device.device.daily_profit_from,
            device.device.daily_profit_to
        )

        device.earnings += earnings_increment
        device.owner.profile.balance += earnings_increment
        device.owner.profile.total_earned += earnings_increment

        today = date.today()
        daily_record, created = DailyEarning.objects.get_or_create(user=device.owner, date=today)
        daily_record.earned += earnings_increment
        daily_record.save()

        device.save()
        device.owner.profile.save()
