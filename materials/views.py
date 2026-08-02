from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import ListView, View
from .models import Material, MaterialStatus
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
        # We calculate statistics on the unfiltered database first for dashboard accuracy
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
        context["selected_worksite_id"] = self.request.GET.get("worksite", "")
        return context

class MaterialCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = MaterialForm(request.POST)
        if form.is_valid():
            mat = form.save()
            return JsonResponse({"success": True, "message": f'Material "{mat.name}" added successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({"success": False, "error": errors})
