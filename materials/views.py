from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import ListView, View
from .models import Material, MaterialStatus, MaterialCatalog
from worksites.models import Worksite
from decimal import Decimal

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["name", "worksite", "quantity", "unit", "unit_price", "supplier", "status"]

class MaterialListView(LoginRequiredMixin, ListView):
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

class MaterialCreateView(LoginRequiredMixin, View):
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
