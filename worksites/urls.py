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
    path("<int:pk>/documents/upload/", views.WorksiteDocumentUploadView.as_view(), name="document_upload"),
    path("documents/<int:pk>/delete/", views.WorksiteDocumentDeleteView.as_view(), name="document_delete"),
    path("<int:pk>/", views.WorksiteDetailView.as_view(), name="detail"),
]
