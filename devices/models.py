from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class DeviceModel(models.Model):
    name = models.CharField(max_length=50)
    desc = models.TextField()
    image = models.ImageField(upload_to="devices/", null=True)
    hashrate = models.FloatField(help_text="MH/s")
    hashrate_from = models.FloatField(help_text="MH/s", default=95)
    hashrate_to = models.FloatField(help_text="MH/s", default=105)
    daily_profit_from = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    daily_profit_to = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    temperature_from = models.FloatField(help_text="Celsius", default=65)
    temperature_to = models.FloatField(help_text="Celsius", default=80)
    wattage = models.IntegerField()
    age = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"
    

class MyDeviceModel(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('maintenance', 'Maintenance'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device = models.ForeignKey(DeviceModel, on_delete=models.CASCADE, related_name="devices")
    hashrate = models.FloatField(help_text="MH/s")
    temperature = models.FloatField(help_text="Celsius")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    earnings = models.DecimalField(max_digits=12, decimal_places=4, default=0.00)
    uptime = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.device_id} ({self.owner.username})"

    def save(self, *args, **kwargs):
        if self.status == 'stopped':
            self.hashrate = 0
            self.temperature = 0
        super().save(*args, **kwargs)
