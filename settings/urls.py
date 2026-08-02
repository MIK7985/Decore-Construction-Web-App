"""
settings URL configuration.
"""
from django.urls import path

from . import views

app_name = "settings"

urlpatterns = [
    path("", views.SettingsView.as_view(), name="index"),
]
