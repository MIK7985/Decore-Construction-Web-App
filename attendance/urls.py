"""
attendance URL configuration.
"""
from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.AttendanceListView.as_view(), name="list"),
    path("sheet/", views.AttendanceSheetView.as_view(), name="sheet"),
    path("create/", views.AttendanceCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.AttendanceUpdateView.as_view(), name="edit"),
]
