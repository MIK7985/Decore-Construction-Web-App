from django.contrib import admin
from .models import Material, MaterialCatalog


@admin.register(MaterialCatalog)
class MaterialCatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "default_unit", "default_unit_price", "default_supplier", "created_at")
    search_fields = ("name", "default_supplier")


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "worksite", "quantity", "unit", "unit_price", "supplier", "status", "created_at")
    list_filter = ("status", "worksite")
    search_fields = ("name", "supplier", "worksite__name")
