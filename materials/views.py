from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View
from django.db import transaction
from .models import Material, MaterialStatus, MaterialCatalog
from worksites.models import Worksite
from decimal import Decimal
from accounts.mixins import EngineerRequiredMixin

class MaterialForm(forms.ModelForm):
    used_quantity = forms.DecimalField(required=False, initial=Decimal("0.00"), max_digits=10, decimal_places=2)

    class Meta:
        model = Material
        fields = ["name", "worksite", "quantity", "used_quantity", "unit", "unit_price", "supplier", "status"]

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        used_quantity = cleaned_data.get("used_quantity")

        if used_quantity is None:
            used_quantity = Decimal("0.00")
            cleaned_data["used_quantity"] = used_quantity

        if quantity is not None:
            if used_quantity > quantity:
                raise forms.ValidationError("Used stock cannot exceed total procured stock.")
            if used_quantity < 0:
                raise forms.ValidationError("Used stock cannot be negative.")
        return cleaned_data

class MaterialListView(LoginRequiredMixin, EngineerRequiredMixin, ListView):
    model = Material
    template_name = "materials/material_list.html"
    context_object_name = "materials"

    def get_queryset(self):
        qs = Material.objects.select_related("worksite")
        worksite_id = self.request.GET.get("worksite")
        if worksite_id and worksite_id.isdigit():
            qs = qs.filter(worksite_id=int(worksite_id))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_materials = Material.objects.all()
        
        total_materials_cost = sum(m.total_cost for m in all_materials)
        delivered_cost = sum(m.total_cost for m in all_materials if m.status == MaterialStatus.DELIVERED)
        pending_cost = sum(m.total_cost for m in all_materials if m.status != MaterialStatus.DELIVERED)
        
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
        form = MaterialForm(request.POST)
        if form.is_valid():
            name_clean = form.cleaned_data["name"].strip()
            unit_clean = form.cleaned_data["unit"].strip()
            worksite = form.cleaned_data["worksite"]
            quantity = form.cleaned_data["quantity"]
            unit_price = form.cleaned_data["unit_price"]
            supplier = form.cleaned_data["supplier"].strip()
            status = form.cleaned_data["status"]

            # Save to Master Catalog if checkbox selected
            if request.POST.get("save_to_catalog") == "1" and name_clean:
                MaterialCatalog.objects.get_or_create(
                    name=name_clean,
                    defaults={
                        "default_unit": unit_clean,
                        "default_unit_price": unit_price,
                        "default_supplier": supplier
                    }
                )

            # Look for an existing material entry at this worksite with matching name & unit (case-insensitive)
            existing = Material.objects.filter(
                worksite=worksite,
                name__iexact=name_clean,
                unit__iexact=unit_clean
            ).first()

            if existing:
                existing.quantity += quantity
                if unit_price and unit_price > 0:
                    existing.unit_price = unit_price
                if supplier:
                    existing.supplier = supplier
                if status:
                    existing.status = status
                existing.save()
                return JsonResponse({
                    "success": True,
                    "message": f'Merged stock! Added {quantity} {unit_clean} to existing {existing.name}. Total stock is now {existing.quantity} {unit_clean} on {worksite.name}.'
                })
            else:
                mat = form.save()
                return JsonResponse({
                    "success": True,
                    "message": f'Material "{mat.name}" ({mat.quantity} {mat.unit}) added successfully!'
                })
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({"success": False, "error": errors})


class MaterialStatusUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        mat = get_object_or_404(Material, pk=pk)
        new_status = request.POST.get("status", "").strip()

        if new_status in [choice.value for choice in MaterialStatus]:
            mat.status = new_status
            mat.save()
            return JsonResponse({
                "success": True,
                "message": f'Updated status of "{mat.name}" to {mat.status}!',
                "status": mat.status
            })
        return JsonResponse({"success": False, "error": "Invalid status option."}, status=400)


class MaterialUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        mat = get_object_or_404(Material, pk=pk)
        form = MaterialForm(request.POST, instance=mat)
        if form.is_valid():
            mat = form.save()
            return JsonResponse({
                "success": True,
                "message": f'Material "{mat.name}" updated successfully!'
            })
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({"success": False, "error": errors})


class MaterialDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        mat = get_object_or_404(Material, pk=pk)
        name = mat.name
        mat.delete()
        return JsonResponse({"success": True, "message": f'Material "{name}" deleted from inventory.'})


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


class MaterialUsageUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        mat = get_object_or_404(Material, pk=pk)
        try:
            used_qty = Decimal(request.POST.get("used_quantity", "0.00").strip() or "0.00")
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid numeric value for used quantity."}, status=400)

        if used_qty < 0:
            return JsonResponse({"success": False, "error": "Used quantity cannot be negative."}, status=400)
        if used_qty > mat.quantity:
            return JsonResponse({"success": False, "error": "Used quantity cannot exceed total procured quantity."}, status=400)

        mat.used_quantity = used_qty
        mat.save(update_fields=["used_quantity"])

        return JsonResponse({
            "success": True,
            "message": f'Successfully updated usage for "{mat.name}". Balance: {mat.balance_quantity} {mat.unit}.',
            "used_quantity": float(mat.used_quantity),
            "balance_quantity": float(mat.balance_quantity)
        })


class MaterialBulkCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        import json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                worksite_id = data.get("worksite")
                items = data.get("items", [])
            except Exception:
                return JsonResponse({"success": False, "error": "Invalid JSON format."}, status=400)
        else:
            worksite_id = request.POST.get("worksite")
            names = request.POST.getlist("name[]")
            quantities = request.POST.getlist("quantity[]")
            units = request.POST.getlist("unit[]")
            unit_prices = request.POST.getlist("unit_price[]")
            suppliers = request.POST.getlist("supplier[]")
            statuses = request.POST.getlist("status[]")
            
            items = []
            for i in range(len(names)):
                if not names[i].strip():
                    continue
                items.append({
                    "name": names[i],
                    "quantity": quantities[i] if i < len(quantities) else "0",
                    "unit": units[i] if i < len(units) else "",
                    "unit_price": unit_prices[i] if i < len(unit_prices) else "0",
                    "supplier": suppliers[i] if i < len(suppliers) else "",
                    "status": statuses[i] if i < len(statuses) else "Delivered",
                })

        if not worksite_id:
            return JsonResponse({"success": False, "error": "Worksite is required."}, status=400)
        
        worksite = get_object_or_404(Worksite, id=worksite_id)
        created_count = 0
        merged_count = 0

        with transaction.atomic():
            for item in items:
                name_clean = item.get("name", "").strip()
                if not name_clean:
                    continue
                
                unit_clean = item.get("unit", "").strip()
                try:
                    quantity = Decimal(str(item.get("quantity", "0")).strip() or "0")
                except Exception:
                    quantity = Decimal("0.00")
                
                try:
                    unit_price = Decimal(str(item.get("unit_price", "0")).strip() or "0")
                except Exception:
                    unit_price = Decimal("0.00")
                    
                supplier = item.get("supplier", "").strip()
                status = item.get("status", "Delivered")

                # Check if we should merge with existing
                existing = Material.objects.filter(
                    worksite=worksite,
                    name__iexact=name_clean,
                    unit__iexact=unit_clean
                ).first()

                if existing:
                    existing.quantity += quantity
                    if unit_price > 0:
                        existing.unit_price = unit_price
                    if supplier:
                        existing.supplier = supplier
                    if status:
                        existing.status = status
                    existing.save()
                    merged_count += 1
                else:
                    Material.objects.create(
                        worksite=worksite,
                        name=name_clean,
                        unit=unit_clean,
                        quantity=quantity,
                        unit_price=unit_price,
                        supplier=supplier,
                        status=status
                    )
                    created_count += 1

        return JsonResponse({
            "success": True,
            "message": f"Successfully logged {created_count} new material(s) and updated {merged_count} existing item(s) at {worksite.name}."
        })
