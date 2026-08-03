from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Worksite, WorksiteDocument, DocumentCategory
from employees.models import Employee
from django import forms

class WorksiteForm(forms.ModelForm):
    class Meta:
        model = Worksite
        fields = ['name', 'client', 'location', 'supervisor', 'status', 'progress', 'budget', 'spend', 'start_date', 'client_paid']

class WorksiteListView(LoginRequiredMixin, ListView):
    model = Worksite
    template_name = "worksites/worksite_list.html"
    context_object_name = "worksites"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worksites = self.get_queryset()
        
        total_income = sum(w.budget for w in worksites)
        total_expenses = sum(w.total_spend for w in worksites)
        total_profit = total_income - total_expenses
        profit_margin = (total_profit / total_income * 100) if total_income > 0 else 0

        total_client_paid = sum(w.client_paid for w in worksites)
        total_client_balance = sum(w.client_balance for w in worksites)

        context['stats'] = {
            'total': worksites.count(),
            'active': worksites.filter(status='active').count(),
            'on_hold': worksites.filter(status='on_hold').count(),
            'completed': worksites.filter(status='completed').count(),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'total_profit': total_profit,
            'total_profit_abs': abs(total_profit),
            'profit_margin': profit_margin,
            'total_client_paid': total_client_paid,
            'total_client_balance': total_client_balance,
        }
        context['supervisors_list'] = User.objects.all()
        return context

class WorksiteCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = WorksiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            return JsonResponse({'success': True, 'message': f'Worksite "{site.name}" created successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class WorksiteUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        form = WorksiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            return JsonResponse({'success': True, 'message': f'Worksite "{site.name}" updated successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class WorksiteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        name = site.name
        site.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Worksite "{name}" deleted successfully!'})
        return redirect('worksites:list')

class WorksiteDetailView(LoginRequiredMixin, DetailView):
    model = Worksite
    template_name = "worksites/worksite_detail.html"
    context_object_name = "worksite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assigned_employees'] = self.object.employees.all()
        context['materials'] = self.object.materials.all()
        context['documents'] = self.object.documents.all()
        context['document_categories'] = DocumentCategory.choices
        return context


class WorksiteDocumentUploadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        title = request.POST.get("title", "").strip()
        category = request.POST.get("category", DocumentCategory.OTHER)
        notes = request.POST.get("notes", "").strip()
        file_obj = request.FILES.get("file")

        if not file_obj:
            return JsonResponse({"success": False, "error": "Please select a file to upload."}, status=400)
        
        if not title:
            title = file_obj.name

        doc = WorksiteDocument.objects.create(
            worksite=site,
            title=title,
            category=category,
            file=file_obj,
            file_size=file_obj.size,
            notes=notes,
            uploaded_by=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({
            "success": True,
            "message": f'Document "{doc.title}" uploaded successfully!'
        })


class WorksiteDocumentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        doc = get_object_or_404(WorksiteDocument, pk=pk)
        title = doc.title
        site_pk = doc.worksite.pk
        doc.file.delete(save=False)
        doc.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Document "{title}" deleted successfully!'})
        return redirect('worksites:detail', pk=site_pk)
