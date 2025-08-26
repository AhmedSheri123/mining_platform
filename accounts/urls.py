from django.urls import path
from . import views

urlpatterns = [
    path('Signup', views.Signup, name='Signup'),
    path('Login', views.Login, name='Login'),
    path('Logout', views.Logout, name='Logout'),
    path('EditProfile', views.EditProfile, name='EditProfile'),

    path('transactions/', views.transactions, name='transactions'),
    path('referral_dashboard/', views.referral_dashboard, name='referral_dashboard'),
    path("deposit/", views.deposit_view, name="deposit"),
    path("webhook/deposit/", views.tron_webhook, name="tron_webhook"),
    path("transfer_to_master/<int:wallet_id>/", views.transfer_to_master_view, name="transfer_to_master"),

]