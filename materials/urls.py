from django.urls import path
from . import views

app_name = "materials"

urlpatterns = [
    path("", views.MaterialListView.as_view(), name="list"),
    path("create/", views.MaterialCreateView.as_view(), name="create"),
    path("<int:pk>/status/", views.MaterialStatusUpdateView.as_view(), name="status_update"),
    path("<int:pk>/edit/", views.MaterialUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.MaterialDeleteView.as_view(), name="delete"),
    path("bulk-create/", views.MaterialCreateView.as_view(), name="create"),
    path("catalog/create/", views.MaterialCatalogCreateView.as_view(), name="catalog_create"),
    path("catalog/<int:pk>/edit/", views.MaterialCatalogUpdateView.as_view(), name="catalog_edit"),
    path("catalog/<int:pk>/delete/", views.MaterialCatalogDeleteView.as_view(), name="catalog_delete"),
]
