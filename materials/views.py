from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View
from django.db import transaction
from django.utils import timezone
from .models import Material, MaterialStatus, MaterialCatalog, MaterialDelivery
from worksites.models import Worksite
from decimal import Decimal
from accounts.mixins import EngineerRequiredMixin

class MaterialListView(LoginRequiredMixin, EngineerRequiredMixin, ListView):
    model = MaterialDelivery
    template_name = "materials/material_list.html"
    context_object_name = "deliveries"

    def get_queryset(self):
        qs = MaterialDelivery.objects.select_related("worksite").prefetch_related("items")
        worksite_id = self.request.GET.get("worksite")
        if worksite_id and worksite_id.isdigit():
            qs = qs.filter(worksite_id=int(worksite_id))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_deliveries = MaterialDelivery.objects.prefetch_related("items").all()
        
        total_materials_cost = sum(d.total_cost for d in all_deliveries)
        delivered_cost = sum(d.total_cost for d in all_deliveries if d.status == MaterialStatus.DELIVERED)
        pending_cost = sum(d.total_cost for d in all_deliveries if d.status != MaterialStatus.DELIVERED)
        
        context["stats"] = {
            "total_materials_cost": total_materials_cost,
            "delivered_cost": delivered_cost,
            "pending_cost": pending_cost,
        }
        context["worksites"] = Worksite.objects.order_by("name")
        context["catalog_items"] = MaterialCatalog.objects.order_by("name")
        context["selected_worksite_id"] = self.request.GET.get("worksite", "")
        return context

class MaterialCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        worksite_id = request.POST.get("worksite")
        supplier = request.POST.get("supplier", "").strip()
        status = request.POST.get("status", "Delivered")
        delivery_date_str = request.POST.get("delivery_date")
        
        names = request.POST.getlist("name[]")
        quantities = request.POST.getlist("quantity[]")
        units = request.POST.getlist("unit[]")
        unit_prices = request.POST.getlist("unit_price[]")

        if not worksite_id:
            return JsonResponse({"success": False, "error": "Worksite is required."}, status=400)
        if not supplier:
            return JsonResponse({"success": False, "error": "Supplier is required."}, status=400)

        worksite = get_object_or_404(Worksite, id=worksite_id)
        
        try:
            if delivery_date_str:
                delivery_date = timezone.datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            else:
                delivery_date = timezone.localdate()
        except Exception:
            delivery_date = timezone.localdate()

        items = []
        for i in range(len(names)):
            name_clean = names[i].strip()
            if not name_clean:
                continue
            
            unit_clean = units[i].strip() if i < len(units) else ""
            try:
                quantity = Decimal(str(quantities[i]).strip() or "0")
            except Exception:
                quantity = Decimal("0.00")
            
            try:
                unit_price = Decimal(str(unit_prices[i]).strip() or "0")
            except Exception:
                unit_price = Decimal("0.00")
                
            items.append({
                "name": name_clean,
                "quantity": quantity,
                "unit": unit_clean,
                "unit_price": unit_price
            })

        if not items:
            return JsonResponse({"success": False, "error": "At least one material item is required."}, status=400)

        with transaction.atomic():
            delivery = MaterialDelivery.objects.create(
                worksite=worksite,
                supplier=supplier,
                status=status,
                delivery_date=delivery_date
            )
            for item in items:
                # Save to catalog for future auto-populate auto-reuse
                MaterialCatalog.objects.get_or_create(
                    name=item["name"],
                    defaults={
                        "default_unit": item["unit"],
                        "default_unit_price": item["unit_price"],
                        "default_supplier": supplier
                    }
                )
                Material.objects.create(
                    delivery=delivery,
                    name=item["name"],
                    quantity=item["quantity"],
                    unit=item["unit"],
                    unit_price=item["unit_price"]
                )

        return JsonResponse({
            "success": True,
            "message": f"Successfully logged delivery of {len(items)} items from {supplier} to {worksite.name}."
        })

class MaterialStatusUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        delivery = get_object_or_404(MaterialDelivery, pk=pk)
        new_status = request.POST.get("status", "").strip()

        if new_status in [choice.value for choice in MaterialStatus]:
            delivery.status = new_status
            delivery.save(update_fields=["status"])
            return JsonResponse({
                "success": True,
                "message": f"Updated status of delivery to {delivery.status}!",
                "status": delivery.status
            })
        return JsonResponse({"success": False, "error": "Invalid status option."}, status=400)

class MaterialUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        delivery = get_object_or_404(MaterialDelivery, pk=pk)
        supplier = request.POST.get("supplier", "").strip()
        status = request.POST.get("status", "").strip()
        delivery_date_str = request.POST.get("delivery_date")

        if supplier:
            delivery.supplier = supplier
        if status in [choice.value for choice in MaterialStatus]:
            delivery.status = status
        if delivery_date_str:
            try:
                delivery.delivery_date = timezone.datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
            except Exception:
                pass
        
        delivery.save()
        return JsonResponse({"success": True, "message": "Delivery details updated successfully."})

class MaterialDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        delivery = get_object_or_404(MaterialDelivery, pk=pk)
        supplier = delivery.supplier
        delivery.delete()
        return JsonResponse({"success": True, "message": f"Delivery from {supplier} deleted successfully."})


class MaterialCatalogCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        default_unit = request.POST.get("default_unit", "").strip()
        default_unit_price = request.POST.get("default_unit_price", "0")
        default_supplier = request.POST.get("default_supplier", "").strip()

        if not name or not default_unit:
            return JsonResponse({"success": False, "error": "Material Name and Default Unit are required."}, status=400)

        try:
            price = Decimal(str(default_unit_price))
        except Exception:
            price = Decimal("0.00")

        cat, created = MaterialCatalog.objects.get_or_create(
            name=name,
            defaults={
                "default_unit": default_unit,
                "default_unit_price": price,
                "default_supplier": default_supplier
            }
        )

        if not created:
            cat.default_unit = default_unit
            cat.default_unit_price = price
            if default_supplier:
                cat.default_supplier = default_supplier
            cat.save()

        return JsonResponse({
            "success": True,
            "message": f'Master Material "{cat.name}" saved to Catalog!',
            "catalog_item": {
                "id": cat.id,
                "name": cat.name,
                "default_unit": cat.default_unit,
                "default_unit_price": float(cat.default_unit_price),
                "default_supplier": cat.default_supplier
            }
        })


class MaterialCatalogUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        cat = get_object_or_404(MaterialCatalog, pk=pk)
        name = request.POST.get("name", "").strip()
        default_unit = request.POST.get("default_unit", "").strip()
        default_unit_price = request.POST.get("default_unit_price", "0")
        default_supplier = request.POST.get("default_supplier", "").strip()

        if not name or not default_unit:
            return JsonResponse({"success": False, "error": "Material Name and Default Unit are required."}, status=400)

        try:
            price = Decimal(str(default_unit_price))
        except Exception:
            price = Decimal("0.00")

        cat.name = name
        cat.default_unit = default_unit
        cat.default_unit_price = price
        cat.default_supplier = default_supplier
        cat.save()

        return JsonResponse({
            "success": True,
            "message": f'Master Material "{cat.name}" updated successfully!',
            "catalog_item": {
                "id": cat.id,
                "name": cat.name,
                "default_unit": cat.default_unit,
                "default_unit_price": float(cat.default_unit_price),
                "default_supplier": cat.default_supplier
            }
        })


class MaterialCatalogDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        cat = get_object_or_404(MaterialCatalog, pk=pk)
        name = cat.name
        cat.delete()
        return JsonResponse({"success": True, "message": f'Master Material "{name}" removed from catalog.'})



