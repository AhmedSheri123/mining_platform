# users/models.py
from django.db import models
from django.contrib.auth.models import User
from .wallet import get_usdt_balance
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_earned = models.DecimalField(max_digits=12, decimal_places=4, default=0)  # الأرباح الإجمالية
    img_base64 = models.TextField(null=True, blank=True)
    # كود الدعوة الفريد لكل مستخدم
    invite_code = models.CharField(max_length=12, unique=True, blank=True)
    
    # ربط المستخدم بمن دعاهم عند التسجيل
    referred_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals")
    # حقل موثوق
    is_verified = models.BooleanField(default=False, help_text="هل المستخدم موثوق به؟")

    def save(self, *args, **kwargs):
        if not self.invite_code:
            # إنشاء كود دعوة فريد عند إنشاء المستخدم
            self.invite_code = self.get_new_invite_code
        super().save(*args, **kwargs)
    
    @property
    def get_new_invite_code(self):
        return str(uuid.uuid4()).replace("-", "")[:6].upper()

    @property
    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    @property
    def get_is_verified(self):
        r = False if not self.referred_by else self.referred_by.is_superuser
        return r
    
    def __str__(self):
        return f'{self.user.id} - {self.user.username} - {self.get_full_name}' 
    
class DailyEarning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    earned = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} : {self.earned}"
    

    
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('withdraw', 'سحب/تحويل خارجي (USDT)'),
        ('transfer', 'تحويل داخلي'),
    )

    STATUS_CHOICES = (
        ('pending', 'معلق'),
        ('approved', 'موافق'),
        ('rejected', 'مرفوض'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # التحويل الداخلي
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_transfers')

    # السحب/التحويل الخارجي
    wallet_address = models.CharField(max_length=255, null=True, blank=True)

    # حالة الموافقة (معلقة، موافق، مرفوض) فقط للسحب/خارجي
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.transaction_type == 'transfer' and self.to_user:
            return f"{self.user.username} → {self.to_user.username} : {self.amount} USDT"
        elif self.transaction_type == 'withdraw' and self.wallet_address:
            return f"{self.user.username} → external {self.wallet_address} : {self.amount} USDT ({self.get_status_display()})"
        return f"{self.user.username} {self.transaction_type} : {self.amount} USDT ({self.get_status_display()})"



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name="wallet", null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    address = models.CharField(max_length=255, unique=True)
    private_key = models.TextField()  # لا تحتاج (1) هنا
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.balance} USDT"

    def get_blockchain_balance(self):
        return get_usdt_balance(self.address)
    
    

class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'تم التأكيد'),
        ('rejected', 'مرفوض'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    txid = models.CharField(max_length=100, unique=True)   # <--- معرف المعاملة
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.amount} USDT - {self.status}"




class ReferralBonus(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referral_bonuses")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earned_from_referral")
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.referrer.username} earned {self.amount} from {self.referred_user.username}"