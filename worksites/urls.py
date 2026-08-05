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
    path("<int:pk>/payments/create/", views.ClientPaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/delete/", views.ClientPaymentDeleteView.as_view(), name="payment_delete"),
    path("<int:pk>/logs/create/", views.DailySiteLogCreateView.as_view(), name="daily_log_create"),
    path("logs/<int:pk>/delete/", views.DailySiteLogDeleteView.as_view(), name="daily_log_delete"),
    path("<int:pk>/assign-crew/", views.WorksiteAssignCrewView.as_view(), name="assign_crew"),
    path("employees/<int:pk>/unassign/", views.WorksiteUnassignCrewView.as_view(), name="unassign_crew"),
    path("<int:pk>/", views.WorksiteDetailView.as_view(), name="detail"),
]
