from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required


from django.db.models import Sum, Count
from accounts.models import UserProfile, Transaction, DailyEarning, Deposit, Wallet
from django.contrib.auth.models import User
from devices.models import MyDeviceModel
from django.http import JsonResponse
from decimal import Decimal
from django.contrib import messages
from django.utils.timezone import now
from .forms import UserEditForm, UserProfileEditForm
from django.utils import timezone
from datetime import timedelta
# شرط: الدخول فقط للمستخدمين من نوع staff أو superuser
def is_admin(user):
    return user.is_staff or user.is_superuser

def three_days_balance_chart(request):
    # تاريخ اليوم وتاريخ قبل 3 أيام
    today = timezone.now().date()
    three_days_ago = today - timedelta(days=2)  # يشمل اليوم + اليومين السابقين

    chart_labels = []
    balance_data = []
    deposits_data = []

    for i in range(30):
        day = three_days_ago + timedelta(days=i)
        chart_labels.append(day.strftime("%Y-%m-%d"))

        # اجمالي الرصيد الكلي للمستخدمين في ذلك اليوم
        # هنا نفترض الرصيد النهائي لكل يوم (يمكنك تعديل حسب بياناتك)
        balance_total = float(DailyEarning.objects.filter(date=day)
            .aggregate(total=Sum('earned'))['total'] or 0
        )
        balance_data.append(balance_total)

        # اجمالي الإيداعات في ذلك اليوم
        deposits_total = float(
            Deposit.objects.filter(created_at__date=day)
            .aggregate(total=Sum('amount'))['total'] or 0
        )
        deposits_data.append(deposits_total)

    return {
        'chart_labels': chart_labels,
        'balance_data': balance_data,
        'deposits_data': deposits_data,
    }


@user_passes_test(is_admin)
def home(request):
    today = now().date()

    # الإحصائيات العامة
    total_users = UserProfile.objects.count()
    total_balance = UserProfile.objects.aggregate(total=Sum("balance"))["total"] or 0
    total_earnings = UserProfile.objects.aggregate(total=Sum("total_earned"))["total"] or 0
    total_deposit_earnings = Deposit.objects.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
    total_transaction_earnings = Transaction.objects.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
    active_devices = MyDeviceModel.objects.filter(status="running").count()
    total_devices = MyDeviceModel.objects.count()


    # إحصائيات اليوم
    new_users_today = UserProfile.objects.filter(user__date_joined__date=today).count()
    earnings_today = DailyEarning.objects.filter(date=today).aggregate(total=Sum("earned"))["total"] or 0
    deposit_earnings_today = Deposit.objects.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
    transaction_earnings_today = Transaction.objects.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0
    buyed_devices_today = MyDeviceModel.objects.filter(created_at__date=today).count()
    transactions_today = Transaction.objects.filter(created_at__date=today).count()


    latest_users = UserProfile.objects.order_by("-id")[:5]
    latest_transactions = Transaction.objects.order_by("-id")[:5]
    latest_deposits = Deposit.objects.order_by("-id")[:5]

    difference = total_deposit_earnings - total_earnings
    difference_chart_labels = ['الرصيد الكلي للمستخدمين', 'إجمالي الإيداعات', 'الفارق']
    difference_chart_data = [float(total_earnings), float(total_deposit_earnings), float(difference)]

    context = {
        'difference_chart_labels': difference_chart_labels,
        'difference_chart_data': difference_chart_data,

        "total_users": total_users,
        "total_balance": total_balance,
        "total_earnings": total_earnings,
        "total_transaction_earnings":total_transaction_earnings,
        "total_deposit_earnings":total_deposit_earnings,
        "active_devices": active_devices,
        "total_devices": total_devices,


        "new_users_today": new_users_today,
        "earnings_today": earnings_today,
        "deposit_earnings_today":deposit_earnings_today,
        "transaction_earnings_today":transaction_earnings_today,
        "buyed_devices_today": buyed_devices_today,
        "transactions_today": transactions_today,
        
        "latest_users": latest_users,
        "latest_transactions": latest_transactions,
        "latest_deposits":latest_deposits,
    }

    context.update(three_days_balance_chart(request))
    return render(request, "management/home.html", context)





def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.get(user=user)

    # أرباح المستخدم
    total_earnings = profile.total_earned

    # الإيداعات
    total_deposits = Deposit.objects.filter(wallet__user=user).aggregate(total=Sum("amount"))["total"] or 0

    # السحوبات
    total_withdrawals = Transaction.objects.filter(user=user, transaction_type="withdraw", status="approved").aggregate(total=Sum("amount"))["total"] or 0
    total_pending_withdrawals = Transaction.objects.filter(user=user, transaction_type="withdraw", status="pending").aggregate(total=Sum("amount"))["total"] or 0

    devices = MyDeviceModel.objects.filter(owner=user)
    context = {
        "user_obj": user,
        "profile": profile,
        "total_earnings": total_earnings,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "total_pending_withdrawals": total_pending_withdrawals,
        "devices": devices,
        "total_devices": devices.count(),
    }
    return render(request, "management/users/user_detail.html", context)





# صفحة المستخدمين
def users_view(request):
    users = User.objects.all().order_by('-date_joined')
    
    users_data = []
    for u in users:
        profile = getattr(u, 'profile', None)
        if profile:
            total_earnings = profile.total_earned
        else:
            total_earnings = 0

        total_deposits = Deposit.objects.filter(wallet__user=u).aggregate(total=Sum('amount'))['total'] or 0
        total_withdrawals = Transaction.objects.filter(user=u, transaction_type='withdraw', status="approved")
        total_devices = MyDeviceModel.objects.filter(owner=u).count()
        total_pending_withdrawals = Transaction.objects.filter(user=u, transaction_type="withdraw", status="pending").aggregate(total=Sum("amount"))["total"] or 0
        
        users_data.append({
            'id': u.id,
            'user':u,
            'username': u.username,
            'email': u.email,
            'total_balance': u.profile.balance,
            'total_earnings': total_earnings,
            'total_deposits': total_deposits,
            'total_withdrawals_mod': total_withdrawals,
            'total_withdrawals': total_withdrawals.aggregate(total=Sum('amount'))['total'] or 0,
            'total_pending_withdrawals': total_pending_withdrawals,
            'date_joined': u.date_joined,
            'total_devices':total_devices,
        })
    
    context = {
        'users': users_data
    }
    return render(request, 'management/users/users.html', context)


# تحديث بيانات المستخدمين للأجاكس
def users_status(request):
    users = User.objects.all()
    data = []
    for u in users:
        profile = getattr(u, 'profile', None)
        if profile:
            total_earnings = profile.total_earned
        else:
            total_earnings = 0

        total_deposits = Deposit.objects.filter(wallet__user=u).aggregate(total=Sum('amount'))['total'] or 0
        total_withdrawals = Transaction.objects.filter(user=u, transaction_type='withdraw', status="approved").aggregate(total=Sum('amount'))['total'] or 0
        total_devices = MyDeviceModel.objects.filter(owner=u).count()
        total_pending_withdrawals = Transaction.objects.filter(user=u, transaction_type="withdraw", status="pending").aggregate(total=Sum("amount"))["total"] or 0
        
        data.append({
            'id': u.id,
            'total_balance': u.profile.balance,
            'total_earnings': float(total_earnings),
            'total_deposits': float(total_deposits),
            'total_withdrawals': float(total_withdrawals),
            'total_pending_withdrawals': float(total_pending_withdrawals),
            'total_devices':total_devices,
        })
    return JsonResponse({'users': data})





@login_required
@user_passes_test(is_admin)
def transactions_dashboard(request):
    # كل التحويلات (يمكن تصفية حسب النوع)
    withdrawals = Transaction.objects.filter(transaction_type='withdraw').order_by('-created_at')
    deposits = Transaction.objects.filter(transaction_type='transfer').order_by('-created_at')

    context = {
        'withdrawals': withdrawals,
        'deposits': deposits,
    }
    return render(request, 'management/transactions/transactions.html', context)

@login_required
@user_passes_test(is_admin)
def approve_withdrawal(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, transaction_type='withdraw')
    user = transaction.user
    profile = user.profile
    # التأكد أن الرصيد يكفي لشراء الجهاز
    if transaction.user.profile.balance < transaction.amount:
        messages.error(request, f"رصيد المستخدم غير كافي: {transaction.user.profile.balance} دولار")
        return redirect('transactions_dashboard')

    # خصم سعر الجهاز من رصيد المستخدم
    profile.balance -= Decimal(transaction.amount)
    profile.save()
    
    transaction.status = 'approved'
    transaction.save()
    device = user.devices.all().first()
    device.stop_continue = False
    device.save()
    return redirect('transactions_dashboard')

@login_required
@user_passes_test(is_admin)
def reject_withdrawal(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, transaction_type='withdraw')
    transaction.status = 'rejected'
    transaction.save()
    return redirect('transactions_dashboard')





@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile_obj = getattr(user_obj, 'profile', None)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user_obj)
        profile_form = UserProfileEditForm(request.POST, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'تم تحديث بيانات المستخدم بنجاح!')
            return redirect('user_detail', user_id=user_obj.id)
    else:
        user_form = UserEditForm(instance=user_obj)
        profile_form = UserProfileEditForm(instance=profile_obj)

    context = {
        'user_obj': user_obj,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'management/users/edit_user.html', context)


@staff_member_required  # يسمح فقط للـ admin أو staff
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    
    username = user_obj.username
    user_obj.delete()
    messages.success(request, f"تم حذف المستخدم {username} بنجاح.")
    return redirect('users')  # اسم صفحة قائمة المستخدمين




@login_required
@staff_member_required
def change_device_status(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        new_status = request.POST.get('new_status')
        
        device = MyDeviceModel.objects.filter(id=device_id).first()
        if not device:
            return JsonResponse({'success': False, 'message': 'الجهاز غير موجود.'})
        
        if new_status not in dict(MyDeviceModel.STATUS_CHOICES):
            return JsonResponse({'success': False, 'message': 'الحالة غير صالحة.'})
        
        device.status = new_status
        device.save()
        
        return JsonResponse({'success': True, 'status': device.status})
    
    return JsonResponse({'success': False, 'message': 'طريقة الطلب غير مدعومة.'})


def wallets_list(request):
    # جلب جميع المحافظ وترتيبها حسب الرصيد الأعلى
    wallets = Wallet.objects.all().order_by('-balance')

    context = {
        'wallets': wallets,
    }
    return render(request, 'management/transactions/wallets_list.html', context)


def deposit_list(request, wallet_id):
    # جلب جميع المحافظ وترتيبها حسب الرصيد الأعلى
    deposits = Deposit.objects.filter(wallet__id=wallet_id).order_by('-id')

    context = {
        'deposits': deposits,
    }
    return render(request, 'management/transactions/deposit_list.html', context)