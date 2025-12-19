from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Transaction, Deposit, Wallet, UserProfile, ReferralBonus
from accounts.utils import transfer  # نترك transfer للتحويل الداخلي
from django.contrib.auth.models import User
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, requests
import qrcode
import base64
from io import BytesIO
from django.contrib.auth import logout, login, authenticate
from django.http import JsonResponse
from .wallet import USDT_CONTRACT, get_trx_balance, transfer_to_master, transfer_trx
from .forms import UserSignUpModelForm, LoginForm, UserEditModelForm
from .utils import RandomDigitsGen
from django.db import models
from devices.models import MyDeviceModel, DeviceModel

def Main(request):
    return render(request, 'accounts/main.html')

def Signup(request):
    user_form = UserSignUpModelForm()

    if request.method == 'POST':
        invite_code = request.POST.get('invite_code')
        referrer_profiles = UserProfile.objects.filter(invite_code=invite_code)

        user_form = UserSignUpModelForm(data=request.POST)
        if referrer_profiles.exists():
            
            if user_form.is_valid():
                password = user_form.cleaned_data.get('password')

                user = user_form.save(commit=False)
                # user.username = RandomDigitsGen()
                user.set_password(password)

                user.save()
                # ربط المستخدم بالشخص الذي دعاه
                referrer_profile = referrer_profiles.first()
                user.profile.referred_by = referrer_profile.user
                user.profile.save()
                if referrer_profile.user.is_superuser:
                    referrer_profile.invite_code = referrer_profile.get_new_invite_code
                    referrer_profile.save()


                device = DeviceModel.objects.get(stage=1) if user.profile.get_is_verified else DeviceModel.objects.get(stage=1, view_for_not_verified=True)
                MyDeviceModel.objects.create(
                    owner=user,
                    device=device,
                    status='stopped'
                )

                ReferralBonus.objects.create(
                    referrer=referrer_profile.user,
                    referred_user=user,
                    amount=0  # قيمة المكافأة
                )

                messages.success(request, 'Account Created Successfully')
                return redirect('Login')
            else:messages.error(request, user_form.errors)
        else:messages.warning(request, "كود الدعوة غير صحيح")
                        

    return render(request, 'accounts/signup.html', {'user_form':user_form})

def Login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            users = User.objects.filter(username=username)
            if users.exists():
                user = users.first()
                user = authenticate(username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Login Success')
                    return redirect('dashboard')
                else:messages.error(request, 'wrong email or password')
            else:messages.error(request, 'user dos not exists')
        else:messages.error(request, form.errors)
    return render(request, 'accounts/login.html', {'form':form})

def Logout(request):
    logout(request)
    return redirect('Login')

def EditProfile(request):
    user = request.user
    userprofile = user.profile

    user_form = UserEditModelForm(instance=user)
    if request.method == 'POST':
        profile_img = request.POST.get('profile_img')
        user_form = UserEditModelForm(data=request.POST, instance=user)
        user_form.fields.pop('password')
        if user_form.is_valid():
            user_form.save()
            userprofile = user.profile
            userprofile.img_base64 = profile_img
            userprofile.save()
        else:
            if user_form.errors:
                messages.error(request, user_form.errors)

    return render(request, 'accounts/profile/EditProfile.html', {'user_form':user_form})






def transactions(request):
    user = request.user
    transactions = user.transactions.all().order_by('-created_at')
    device = MyDeviceModel.objects.get(owner=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        amount = Decimal(request.POST.get('amount', '0'))
        
        if action == 'withdraw':
            wallet_address = request.POST.get('wallet_address', '').strip()
            if device.status == 'done':
                if amount > 0 and wallet_address:
                    if user.profile.balance >= amount:  # تحقق من الرصيد
                        # إنشاء طلب سحب جديد (معلق)
                        Transaction.objects.create(
                            user=user,
                            transaction_type='withdraw',
                            amount=amount,
                            wallet_address=wallet_address,
                            status='pending'
                        )
                        messages.success(request, f"تم تقديم طلب سحب {amount} USDT، في انتظار الموافقة")
                    else:
                        messages.error(request, "الرصيد غير كافٍ")
                else:
                    messages.error(request, "الرجاء إدخال المبلغ وعنوان المحفظة بشكل صحيح")
            else:
                messages.error(request, "يرجى اكمال المهمات الموجودة لتتمكن من السحب")
        elif action == 'transfer':
            recipient_username = request.POST.get('recipient')
            try:
                recipient = User.objects.get(username=recipient_username)
                if recipient != user:
                    if amount > 0 and user.profile.balance >= amount:
                        # تحويل داخلي مباشر
                        Transaction.objects.create(
                            user=user,
                            transaction_type='transfer',
                            amount=amount,
                            to_user=recipient,
                            status='approved'
                        )
                        # تحديث الأرصدة
                        user.profile.balance -= amount
                        recipient.profile.balance += amount
                        user.profile.save()
                        recipient.profile.save()
                        messages.success(request, f"تم تحويل {amount} USDT إلى {recipient.username}")
                    else:
                        messages.error(request, "الرصيد غير كافٍ أو المبلغ غير صحيح")
                else:messages.error(request, "المستخدم المستلم غير موجود")
            except User.DoesNotExist:
                messages.error(request, "المستخدم المستلم غير موجود")

    context = {
        "transactions": transactions,
        "balance": user.profile.balance,
    }
    return render(request, "dashboard/accounts/transactions/transactions.html", context)



@login_required
def deposit_view(request):
    wallet = request.user.wallet
    deposits = wallet.deposits.all()

    # توليد QR code
    qr = qrcode.make(wallet.address)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    check_deposits(wallet, request)
    return render(request, "dashboard/accounts/transactions/deposit.html", {
        "wallet": wallet,
        "deposits": deposits,
        "qr_code": qr_base64,
    })



@csrf_exempt
def tron_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # مثال لبيانات مرسلة من المزود
        tx_id = data.get("txID")
        to_address = data.get("to")
        from_address = data.get("from")
        amount = Decimal(data.get("amount", "0"))
        token = data.get("token", "").upper()

        # نتأكد أنه USDT و العملية تخص عنوان مستخدم
        if token == "USDT":
            try:
                wallet = Wallet.objects.get(address=to_address)

                # نتأكد أن الإيداع غير مسجل من قبل
                if not Deposit.objects.filter(wallet=wallet, amount=amount, status="confirmed").exists():
                    Deposit.objects.create(
                        wallet=wallet,
                        amount=amount,
                        status="confirmed",
                        confirmed_at=timezone.now()
                    )
                    wallet.balance += amount
                    wallet.total_balance += amount
                    wallet.save()

            except Wallet.DoesNotExist:
                pass

        return JsonResponse({"status": "ok"})

    return JsonResponse({"error": "Invalid request"}, status=400)



def check_deposits(wallet, request):
    try:
        url = f"https://api.trongrid.io/v1/accounts/{wallet.address}/transactions/trc20"
        resp = requests.get(url).json()
    except Exception as e:
        print(f"خطأ عند جلب المعاملات: {e}")
        return

    for tx in resp.get("data", []):
        try:
            to_address = tx.get("to")
            token_address = tx.get("token_info", {}).get("address")
            if to_address != wallet.address or token_address != USDT_CONTRACT:
                continue

            txid = tx["transaction_id"]
            amount = Decimal(tx["value"]) / Decimal(10**6)

            deposit, created = Deposit.objects.get_or_create(
                wallet=wallet,
                txid=txid,
                defaults={"amount": amount, "status": "confirmed"}
            )

            if created:
                print(f"إيداع جديد: {amount} USDT")

                wallet.user.profile.balance += amount
                wallet.user.profile.save()

                wallet.balance += amount
                wallet.save()

                referrer_user = wallet.user.profile.referred_by
                if referrer_user:
                    try:
                        referral_bonus = ReferralBonus.objects.get(
                            referrer=referrer_user,
                            referred_user=wallet.user
                        )
                        bonus_amount = amount * Decimal('0.05')
                        referral_bonus.amount += bonus_amount
                        referral_bonus.save()

                        referrer_user.profile.balance += bonus_amount
                        referrer_user.profile.save()
                    except ReferralBonus.DoesNotExist:
                        pass

                messages.success(request, f"تم الإيداع بنجاح. الرصيد الحالي: {amount} USDT")
        except Exception as e:
            print(f"خطأ في معالجة المعاملة: {e}")


def transfer_to_master_view(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id)
    # r = transfer_to_master(wallet, request)
    # print(r)
    r2 = transfer_trx(wallet, 7)
    print(r2)
    return redirect('wallets_list')




@login_required
def referral_dashboard(request):
    # استدعاء الملف الشخصي للمستخدم
    profile = request.user.profile

    # جميع المكافآت الخاصة بالمستخدم
    referral_bonuses = ReferralBonus.objects.filter(referrer=request.user).order_by('-created_at')

    # إجمالي المكافآت المكتسبة
    total_bonus = referral_bonuses.aggregate(total=models.Sum('amount'))['total'] or 0

    # عدد الدعوات
    total_referrals = referral_bonuses.count()

    context = {
        'profile': profile,
        'referral_bonuses': referral_bonuses,
        'total_bonus': total_bonus,
        'total_referrals': total_referrals,
    }

    return render(request, 'dashboard/accounts/transactions/ReferralBonus.html', context)