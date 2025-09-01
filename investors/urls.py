from django.urls import path
from investors import views

urlpatterns = [
    path("overview", views.dashboard, name="dashboard"),
]