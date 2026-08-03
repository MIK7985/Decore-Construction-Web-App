from django.contrib import admin

from .models import Worksite, WorksiteDocument


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
