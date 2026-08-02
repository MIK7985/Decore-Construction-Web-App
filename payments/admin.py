from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("employee", "amount", "method", "reference_number", "paid_on")
    list_filter = ("method", "paid_on")
    search_fields = ("employee__name", "reference_number")
