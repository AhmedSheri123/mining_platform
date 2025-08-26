from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="management"),
    path('users', views.users_view, name="users"),
    path('users/users_status', views.users_status, name="users_status"),
    path("user/<int:user_id>/", views.user_detail, name="user_detail"),
    path("user/delete/<int:user_id>/", views.delete_user, name="delete_user"),
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),


    path('transactions/', views.transactions_dashboard, name='transactions_dashboard'),
    path('transactions/approve/<int:transaction_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('transactions/reject/<int:transaction_id>/', views.reject_withdrawal, name='reject_withdrawal'),

    path('device/change_status/', views.change_device_status, name='change_device_status'),
    path('wallets_list/', views.wallets_list, name='wallets_list'),
    path('deposit_list/<int:wallet_id>/', views.deposit_list, name='deposit_list'),


]