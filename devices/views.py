from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.wallet import get_usdt_balance
from .models import MyDeviceModel, DeviceModel, DeviceStagesModel
from django.contrib import messages
from decimal import Decimal
from datetime import date
from accounts.models import DailyEarning

@login_required
def devices(request):
    devices = DeviceModel.objects.filter()
    return render(request, "dashboard/devices/devices.html", {"devices": devices})

@login_required
def my_devices(request):
    device = MyDeviceModel.objects.filter(owner=request.user).first()
    return redirect('device_detail', device.id)
    # return render(request, "dashboard/devices/my_devices.html", {"devices": devices})

@login_required
def device_detail(request, pk):
    """
    عرض تفاصيل جهاز محدد للمستخدم الحالي
    """
    owner = request.user
    # جلب الجهاز الخاص بالمستخدم أو 404 إذا لم يكن يملكه
    my_device = get_object_or_404(MyDeviceModel, id=pk, owner=request.user)
    print("$",get_usdt_balance(owner.wallet.address))
    context = {
        "my_device": my_device,
    }

    return render(request, "dashboard/devices/device_detail.html", context)

@login_required
def buy_device(request, pk):
    owner = request.user
    device = get_object_or_404(DeviceModel, pk=pk)

    # التأكد أن الرصيد يكفي لشراء الجهاز
    if owner.profile.balance < device.price:
        messages.error(request, f"رصيدك غير كافي لشراء هذا الجهاز. رصيدك الحالي: {owner.profile.balance} دولار")
        return redirect('devices')

    # خصم سعر الجهاز من رصيد المستخدم
    owner.profile.balance -= Decimal(device.price)
    owner.profile.save()

    # إنشاء الجهاز للمستخدم
    mydevice = MyDeviceModel.objects.create(
        owner=owner,
        device=device,
        hashrate=device.hashrate,
        temperature=28
    )

    messages.success(request, f"تم شراء الجهاز بنجاح! رصيدك المتبقي: {owner.profile.balance} دولار")
    return redirect('my_devices')


@login_required
def devices_status(request):
    """
    إرجاع حالة كل الأجهزة الخاصة بالمستخدم بشكل JSON
    """
    devices = MyDeviceModel.objects.filter(owner=request.user)
    data = []
    for device in devices:
        data.append({
            "id": device.id,
            "device_id": device.device_id,
            "hashrate": float(device.hashrate),
            "temperature": float(device.temperature),
            "status": device.status,
            "earnings": float(device.earnings),
        })
    return JsonResponse({"devices": data})


def stage_data(request, device_id):
    device = get_object_or_404(MyDeviceModel, id=device_id)
    
    return JsonResponse(
        {
            "balance": round(request.user.profile.balance, 2),
            'hashrate':device.hashrate,
            'temperature':device.temperature,
            'wattage':device.wattage,
            'earnings':device.earnings,
        }
    )

def next_stage(request, device_id):
    device = get_object_or_404(MyDeviceModel, id=device_id)
    if device.status == 'done':
        next_stage_model = DeviceStagesModel.objects.get(device__stage=device.device.stage+1, stage=1)
        device.device = next_stage_model.device
        device.stage = 1
        device.stop_continue = True
    else:next_stage_model = DeviceStagesModel.objects.get(device=device.device, stage=device.stage)

    owner = device.owner

    if device.status == 'running':
        messages.error(request, f"الجهاز من قبل قيد التشغيل يرجى الانتظار حتى انتهاء المهمة")
        return redirect('device_detail', device_id)
    # التأكد أن الرصيد يكفي لشراء الجهاز
    if owner.profile.balance < next_stage_model.energy_balance:
        messages.error(request, f"رصيدك غير كافي لشراء هذا الجهاز. رصيدك الحالي: {owner.profile.balance} دولار")
        return redirect('device_detail', device_id)
    
    device.energy_balance = next_stage_model.energy_balance
    device.consumption = 0
    device.status = 'running'
    device.earnings = 0
    device.save()

    owner.profile.balance -= Decimal(next_stage_model.energy_balance)
    owner.profile.save()

    energy_required = float(next_stage_model.energy_balance)
    profit_after = float(next_stage_model.profit_per_energy) * energy_required

    today = date.today()
    daily_record, created = DailyEarning.objects.get_or_create(user=device.owner, date=today)
    daily_record.earned += Decimal(profit_after-energy_required)
    daily_record.save()

    return redirect('device_detail', device_id)



def next_stage_detail_ajax(request, device_id):
    """
    View لإرجاع معلومات المرحلة التالية بصيغة JSON
    """
    device = get_object_or_404(MyDeviceModel, id=device_id)
    next_done_warning = False
    try:
        if device.status == 'done':
            next_done_warning = True
            next_stage_model = DeviceStagesModel.objects.get(device__stage=device.device.stage+1, stage=1)
        else:
            next_stage_model = DeviceStagesModel.objects.get(device=device.device, stage=device.stage)
    except DeviceStagesModel.DoesNotExist:
        return JsonResponse({"error": "لا توجد مرحلة قادمة لهذا الجهاز."})

    stages = DeviceStagesModel.objects.filter(device=next_stage_model.device)
    stages_list = [i.stage for i in stages]
    # stage_now = 1 if device.status == 'done' else (device.stage - 1  if device.status == 'next' else device.stage)
    progress = int(next_stage_model.stage / max(stages_list) * 100)

    energy_required = float(next_stage_model.energy_balance)
    profit_after = float(next_stage_model.profit_per_energy) * energy_required
    
    stage_info = {
        "stage": next_stage_model.stage,
        "progress": progress,
        "stop_continue": device.stop_continue,
        "next_done_warning": next_done_warning,
        "device_name": next_stage_model.device.name,
        "device_img": next_stage_model.device.image.url,
        "energy_required": energy_required,
        "profit_after": round(profit_after, 2),
        "clear_profit": round(profit_after-energy_required, 2),
        "profit_per_energy": float(next_stage_model.profit_per_energy),
        "can_afford": device.owner.profile.balance >= next_stage_model.energy_balance,
        "current_balance": float(device.owner.profile.balance),
    }

    return JsonResponse(stage_info)