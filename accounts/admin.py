from django.contrib import admin
from .models import UserProfile, DailyEarning, Wallet, Deposit
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(DailyEarning)
admin.site.register(Wallet)
admin.site.register(Deposit)