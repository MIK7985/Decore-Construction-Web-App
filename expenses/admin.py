from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "worksite", "amount", "date", "status")
    list_filter = ("category", "status", "date")
    search_fields = ("description", "worksite__name")
