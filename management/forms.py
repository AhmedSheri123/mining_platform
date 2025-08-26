from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_staff']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input mt-2'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input mt-2'}),
        }

class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['balance', 'total_earned', 'invite_code', 'img_base64']
        widgets = {
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_earned': forms.NumberInput(attrs={'class': 'form-control'}),
            'invite_code': forms.TextInput(attrs={'class': 'form-control'}),
            'img_base64': forms.Textarea(attrs={'class': 'form-control', 'rows':3}),
        }