from django.shortcuts import render
from datetime import date, timedelta
from accounts.models import DailyEarning
from decimal import Decimal
from devices.models import MyDeviceModel
# Create your views here.

def dashboard(request):
    user = request.user

    my_devices = MyDeviceModel.objects.filter(owner=user)
    only_runing_devices = my_devices.filter(status='running')

    # الأرباح اليومية اليوم
    today = date.today()
    daily_earning_obj = DailyEarning.objects.filter(user=user, date=today).first()
    daily_earning = daily_earning_obj.earned if daily_earning_obj else Decimal('0.0')

    # الأرباح الشهرية (آخر 30 يوم)
    start_date = today - timedelta(days=29)
    monthly_earnings_qs = DailyEarning.objects.filter(user=user, date__range=[start_date, today])
    monthly_earning = sum(e.earned for e in monthly_earnings_qs)

    context = {
        "my_devices": my_devices,
        "only_runing_devices": only_runing_devices,
        "daily_earning": daily_earning,
        "monthly_earning": monthly_earning,
        "monthly_records": monthly_earnings_qs,  # إذا تريد رسم Chart
    }
    return render(request, "dashboard/home.html", context)