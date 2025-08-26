from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.utils.translation import gettext_lazy as _

class UserSignUpModelForm(forms.ModelForm):
    password = forms.CharField(label='password', max_length=254, widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Password'}))
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']

        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':_('your name...')}),
            'last_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':_('your last name...')}),
            'username': forms.TextInput(attrs={'class':'form-control', 'placeholder':_('name')})
        }


class UserEditModelForm(forms.ModelForm):
    password = forms.CharField(label='password', max_length=254, widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Password'}))
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':_('your name...')}),
            'last_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':_('your last name...')}),
            'email': forms.EmailInput(attrs={'class':'form-control', 'placeholder':_('name@example.com')})
        }


class LoginForm(forms.Form):
    username = forms.CharField(label='username', max_length=254, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':_('name')}))
    password = forms.CharField(label='password', max_length=254, widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':_('Password')}))
