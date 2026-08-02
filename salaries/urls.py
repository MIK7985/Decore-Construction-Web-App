"""
salaries URL configuration.
"""
from django.urls import path

from . import views

app_name = "salaries"

urlpatterns = [
    path("", views.SalaryListView.as_view(), name="list"),
    path("generate/", views.SalaryGenerateView.as_view(), name="generate"),
    path("pay/", views.SalaryPayView.as_view(), name="pay"),
]
