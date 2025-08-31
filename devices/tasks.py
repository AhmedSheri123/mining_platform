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

        result = device.run_stage()
