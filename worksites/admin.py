from django.contrib import admin

from .models import Worksite


@admin.register(Worksite)
class WorksiteAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "status", "progress", "budget", "supervisor", "start_date")
    list_filter = ("status", "supervisor")
    search_fields = ("name", "client", "location")
