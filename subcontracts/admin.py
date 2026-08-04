from django.contrib import admin
from .models import Subcontract, SubcontractPayment

@admin.register(Subcontract)
class SubcontractAdmin(admin.ModelAdmin):
    list_display = ("contractor_name", "phone", "trade", "title", "worksite", "contract_amount", "paid_amount", "balance_amount", "status")
    list_filter = ("status", "trade", "worksite")
    search_fields = ("contractor_name", "phone", "title", "worksite__name")

@admin.register(SubcontractPayment)
class SubcontractPaymentAdmin(admin.ModelAdmin):
    list_display = ("subcontract", "amount", "payment_date", "payment_method", "reference_number")
    list_filter = ("payment_method", "payment_date")
    search_fields = ("subcontract__contractor_name", "reference_number")
