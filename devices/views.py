from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.wallet import get_usdt_balance
from .models import MyDeviceModel, DeviceModel
from django.contrib import messages
from decimal import Decimal


@login_required
def devices(request):
    devices = DeviceModel.objects.filter()
    return render(request, "dashboard/devices/devices.html", {"devices": devices})

@login_required
def my_devices(request):
    devices = MyDeviceModel.objects.filter(owner=request.user)
    
    return render(request, "dashboard/devices/my_devices.html", {"devices": devices})

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


