"""
worksites URL configuration.
"""
from django.urls import path

from . import views

app_name = "worksites"

urlpatterns = [
    path("", views.WorksiteListView.as_view(), name="list"),
    path("create/", views.WorksiteCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.WorksiteUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.WorksiteDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.WorksiteDetailView.as_view(), name="detail"),
]
