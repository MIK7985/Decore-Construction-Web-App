from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "worksite", "date", "status")
    list_filter = ("status", "date", "worksite")
    search_fields = ("employee__name",)
    date_hierarchy = "date"
