# accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import Wallet, UserProfile, ReferralBonus
from devices.models import MyDeviceModel, DeviceModel
from .wallet import wallet_gen

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        wallet = wallet_gen()
        if wallet.get("address") and wallet.get("private_key"):
            Wallet.objects.create(
                user=instance,
                address=wallet.get('address'),  # توليد عنوان عشوائي
                private_key=wallet.get('private_key')  # توليد عنوان عشوائي
            )
        UserProfile.objects.create(
            user=instance,
        )
        try:
            device = DeviceModel.objects.get(stage=1)
            MyDeviceModel.objects.create(
                owner=instance,
                device=device,
                status='stopped'
            )
        except:pass
