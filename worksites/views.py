from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Worksite, WorksiteDocument, DocumentCategory, ClientPayment, DailySiteLog, PaymentMethod
from employees.models import Employee
from django import forms
from decimal import Decimal
from django.utils import timezone
from accounts.mixins import EngineerRequiredMixin

class WorksiteForm(forms.ModelForm):
    class Meta:
        model = Worksite
        fields = ['name', 'client', 'location', 'supervisor', 'status', 'progress', 'budget', 'spend', 'start_date', 'client_paid']

class WorksiteListView(LoginRequiredMixin, EngineerRequiredMixin, ListView):
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

class WorksiteCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = WorksiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            return JsonResponse({'success': True, 'message': f'Worksite "{site.name}" created successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class WorksiteUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        form = WorksiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            return JsonResponse({'success': True, 'message': f'Worksite "{site.name}" updated successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class WorksiteDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        name = site.name
        site.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Worksite "{name}" deleted successfully!'})
        return redirect('worksites:list')

class WorksiteDetailView(LoginRequiredMixin, EngineerRequiredMixin, DetailView):
    model = Worksite
    template_name = "worksites/worksite_detail.html"
    context_object_name = "worksite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assigned_employees'] = self.object.employees.all()
        context['materials'] = []
        context['documents'] = self.object.documents.all()
        context['document_categories'] = DocumentCategory.choices
        context['client_payments'] = self.object.client_payments.all()
        context['daily_logs'] = self.object.daily_logs.all()
        context['payment_methods'] = PaymentMethod.choices
        context['subcontracts'] = self.object.subcontracts.prefetch_related('payments').all()
        return context


class WorksiteDocumentUploadView(LoginRequiredMixin, EngineerRequiredMixin, View):
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


class WorksiteDocumentDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        doc = get_object_or_404(WorksiteDocument, pk=pk)
        title = doc.title
        site_pk = doc.worksite.pk
        doc.file.delete(save=False)
        doc.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Document "{title}" deleted successfully!'})
        return redirect('worksites:detail', pk=site_pk)


class ClientPaymentCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        milestone = request.POST.get("milestone", "").strip()
        amount_str = request.POST.get("amount", "0")
        payment_method = request.POST.get("payment_method", PaymentMethod.BANK_TRANSFER)
        reference_number = request.POST.get("reference_number", "").strip()
        payment_date_str = request.POST.get("payment_date")
        notes = request.POST.get("notes", "").strip()
        receipt_file = request.FILES.get("receipt_file")

        if not milestone:
            return JsonResponse({"success": False, "error": "Milestone Stage is required."}, status=400)

        try:
            clean_amt = str(amount_str).replace(',', '').replace('₹', '').strip()
            amount = Decimal(clean_amt)
            if amount <= 0:
                return JsonResponse({"success": False, "error": "Amount must be greater than 0."}, status=400)
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid payment amount."}, status=400)

        payment_date = payment_date_str if payment_date_str else timezone.now().date()

        payment = ClientPayment.objects.create(
            worksite=site,
            milestone=milestone,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            payment_date=payment_date,
            receipt_file=receipt_file,
            notes=notes,
            logged_by=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({
            "success": True,
            "message": f'Client Payment of ₹{payment.amount} recorded for "{payment.milestone}"!'
        })


class ClientPaymentDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(ClientPayment, pk=pk)
        milestone = payment.milestone
        amount = payment.amount
        if payment.receipt_file:
            payment.receipt_file.delete(save=False)
        payment.delete()
        return JsonResponse({"success": True, "message": f'Payment record of ₹{amount} for "{milestone}" deleted.'})


class DailySiteLogCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        site = get_object_or_404(Worksite, pk=pk)
        title = request.POST.get("title", "").strip()
        notes = request.POST.get("notes", "").strip()
        date_str = request.POST.get("date")
        progress_str = request.POST.get("progress_percent")
        photo = request.FILES.get("photo")

        if not title or not notes:
            return JsonResponse({"success": False, "error": "Log title and notes are required."}, status=400)

        log_date = date_str if date_str else timezone.now().date()
        
        progress = None
        if progress_str and progress_str.isdigit():
            progress = int(progress_str)
            if 0 <= progress <= 100:
                site.progress = progress
                site.save()

        site_log = DailySiteLog.objects.create(
            worksite=site,
            date=log_date,
            title=title,
            notes=notes,
            photo=photo,
            progress_percent=progress,
            logged_by=request.user if request.user.is_authenticated else None
        )
        return JsonResponse({
            "success": True,
            "message": f'Daily Site Log "{site_log.title}" posted successfully!'
        })


class DailySiteLogDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        log_item = get_object_or_404(DailySiteLog, pk=pk)
        title = log_item.title
        if log_item.photo:
            log_item.photo.delete(save=False)
        log_item.delete()
        return JsonResponse({"success": True, "message": f'Daily log "{title}" deleted.'})
