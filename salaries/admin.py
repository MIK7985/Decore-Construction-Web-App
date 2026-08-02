from django.contrib import admin

from .models import SalaryRecord


@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "month", "year", "present_days", "net_salary", "status")
    list_filter = ("year", "month", "status")
    search_fields = ("employee__name",)
