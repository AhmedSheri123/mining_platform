from django.urls import path
from investors import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]