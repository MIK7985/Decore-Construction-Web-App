from django.contrib import admin
from .models import Worksite, WorksiteDocument, ClientPayment, DailySiteLog


@admin.register(Worksite)
class WorksiteAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "status", "progress", "budget", "client_paid", "supervisor", "start_date")
    list_filter = ("status", "supervisor")
    search_fields = ("name", "client", "location")


@admin.register(WorksiteDocument)
class WorksiteDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "worksite", "category", "file_size", "uploaded_by", "uploaded_at")
    list_filter = ("category", "worksite", "uploaded_at")
    search_fields = ("title", "notes", "worksite__name")


@admin.register(ClientPayment)
class ClientPaymentAdmin(admin.ModelAdmin):
    list_display = ("worksite", "milestone", "amount", "payment_method", "payment_date", "logged_by", "created_at")
    list_filter = ("payment_method", "worksite", "payment_date")
    search_fields = ("milestone", "reference_number", "notes", "worksite__name")


@admin.register(DailySiteLog)
class DailySiteLogAdmin(admin.ModelAdmin):
    list_display = ("worksite", "title", "date", "progress_percent", "logged_by", "created_at")
    list_filter = ("worksite", "date")
    search_fields = ("title", "notes", "worksite__name")
