from django.urls import path
from . import views

app_name = "subcontracts"

urlpatterns = [
    path("", views.SubcontractListView.as_view(), name="list"),
    path("create/", views.SubcontractCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.SubcontractUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.SubcontractDeleteView.as_view(), name="delete"),
    path("payments/create/", views.SubcontractPaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/delete/", views.SubcontractPaymentDeleteView.as_view(), name="payment_delete"),
    path("payments/<int:pk>/receipt/pdf/", views.SubcontractPaymentReceiptPdfView.as_view(), name="payment_pdf"),
]
