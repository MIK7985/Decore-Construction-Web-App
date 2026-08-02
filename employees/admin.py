"""
employees admin configuration.

Phase 1 placeholder — no models are registered yet.
TODO: Register employees models with the admin site once they exist.
"""
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "worksite", "phone", "status", "wage", "is_archived")
    list_filter = ("status", "worksite", "is_archived")
    search_fields = ("name", "phone")
