from django.db import models
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
import random


class DeviceModel(models.Model):
    name = models.CharField(max_length=50)
    desc = models.TextField()
    image = models.ImageField(upload_to="devices/", null=True)
    stage = models.IntegerField(default=1)
    hashrate = models.FloatField(help_text="MH/s")
    daily_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    temperature = models.FloatField(help_text="Celsius", default=65)
    wattage = models.IntegerField()
    age = models.IntegerField()
    consumption_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0.05)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DeviceStagesModel(models.Model):
    device = models.ForeignKey(DeviceModel, on_delete=models.CASCADE)
    stage = models.IntegerField()
    energy_balance = models.DecimalField(max_digits=10, decimal_places=2, default=1)  # الطاقة المخصصة للمرحلة
    profit_per_energy = models.DecimalField(max_digits=12, decimal_places=2, default=0.1)  # الأرباح لكل وحدة طاقة

    def __str__(self):
        return f"{self.device.name} - Stage {self.stage}"


class MyDeviceModel(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('next', 'Next'),
        ('done', 'Done'),
        ('maintenance', 'Maintenance'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device = models.ForeignKey(DeviceModel, on_delete=models.CASCADE, related_name="devices")
    stage = models.IntegerField(default=1)
    energy_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # طاقة متاحة للجهاز
    consumption = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wattage = models.FloatField(default=0)
    hashrate = models.FloatField(default=0)
    temperature = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    earnings = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.device.name} ({self.owner.username})"

    def save(self, *args, **kwargs):
        if self.status in ['stopped', 'done', 'next']:
            self.hashrate = 0
            self.wattage = 0
            self.temperature = 0
        super().save(*args, **kwargs)

    def _update_performance(self, energy_used_ratio):
        """تحديث الأداء بناءً على نسبة الطاقة المستهلكة"""
        self.wattage = round(self.device.wattage * (1 + energy_used_ratio * 0.05), 2)
        self.hashrate = round(self.device.hashrate * (1 + energy_used_ratio * 0.05), 2)
        self.temperature = round(self.device.temperature + self.wattage * 0.05, 1)

    def run_stage(self):
        """
        تشغيل المرحلة الحالية:
        - يستهلك الطاقة
        - يحسب الأرباح
        - ينتقل للمرحلة التالية إذا انتهت الطاقة
        - عند انتهاء المرحلة 20، يصبح الجهاز 'done'
        """

        try:
            stage_obj = DeviceStagesModel.objects.get(device=self.device, stage=self.stage)
        except DeviceStagesModel.DoesNotExist:
            return {"error": "Stage not found."}

        if self.energy_balance <= 0:
            return {"error": "Not enough energy to run this stage."}

        # استهلاك الطاقة (يمكن تعديل حسب تصميم المرحلة)
        consumption_unit = self.device.consumption_unit
        if self.energy_balance < consumption_unit:
            consumption_unit = self.energy_balance

        # حساب الأرباح
        profit = stage_obj.profit_per_energy * consumption_unit

        # تحديث رصيد الطاقة
        self.energy_balance -= consumption_unit
        self.consumption += consumption_unit

        # تحديث الأرباح
        self.earnings += profit



        # تحديث الأداء
        energy_ratio = float(consumption_unit / stage_obj.energy_balance)
        energy_ratio = random.uniform(energy_ratio, energy_ratio * 5000)
        self._update_performance(float(energy_ratio))

        # تحديث رصيد المستخدم
        profile = getattr(self.owner, 'profile', None)
        if profile:
            profile.balance += profit
            profile.save()

        # الانتقال للمرحلة التالية إذا انتهت الطاقة
        stages = DeviceStagesModel.objects.filter(device=self.device)
        stages_list = [i.stage for i in stages]
        if self.energy_balance <= 0 :
            if self.stage < max(stages_list):
                self.stage += 1
                # إعادة تعبئة الطاقة للمرحلة الجديدة
                # next_stage = DeviceStagesModel.objects.get(device=self.device, stage=self.stage)
                # self.energy_balance = next_stage.energy_balance
                self.status = 'next'
            else:
                self.status = 'done'
                self.is_completed = True

        self.save()

        return {
            "profit": float(profit),
            "consumption": float(consumption_unit),
            "stage": self.stage,
            "energy_left": float(self.energy_balance),
            "status": self.status,
            "wattage": self.wattage,
            "hashrate": self.hashrate,
            "temperature": self.temperature
        }
