from django.contrib import admin
from .models import Material, MaterialCatalog, MaterialDelivery

class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1

@admin.register(MaterialCatalog)
class MaterialCatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "default_unit", "default_unit_price", "default_supplier", "created_at")
    search_fields = ("name", "default_supplier")

@admin.register(MaterialDelivery)
class MaterialDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "worksite", "supplier", "status", "delivery_date", "created_at")
    list_filter = ("status", "worksite", "delivery_date")
    search_fields = ("supplier", "worksite__name")
    inlines = [MaterialInline]

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "delivery", "quantity", "unit", "unit_price", "created_at")
    list_filter = ("delivery__status", "delivery__worksite")
    search_fields = ("name", "delivery__supplier", "delivery__worksite__name")
