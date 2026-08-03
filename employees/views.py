import re
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Employee, EmployeeStatus
from worksites.models import Worksite
from django import forms
from accounts.mixins import EngineerRequiredMixin

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'role', 'worksite', 'phone', 'wage', 'address', 'status', 'photo', 'id_photo']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        clean_p = re.sub(r'[\s\-\+]', '', phone)
        if clean_p.startswith('91') and len(clean_p) == 12:
            clean_p = clean_p[2:]
            
        if not re.match(r'^[6-9]\d{9}$', clean_p):
            raise forms.ValidationError("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
        return clean_p

class EmployeeListView(LoginRequiredMixin, EngineerRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        show_archived = self.request.GET.get('show_archived') == 'true'
        if show_archived:
            return Employee.objects.filter(is_archived=True).select_related("worksite")
        return Employee.objects.filter(is_archived=False).select_related("worksite")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["worksites"] = Worksite.objects.all()
        context["show_archived"] = self.request.GET.get('show_archived') == 'true'
        return context

class EmployeeCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            emp = form.save()
            return JsonResponse({'success': True, 'message': f'Employee "{emp.name}" registered successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class EmployeeUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        return redirect(f"{reverse('employees:list')}?edit={pk}")

    def post(self, request, pk, *args, **kwargs):
        employee = get_object_or_404(Employee, pk=pk)
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            emp = form.save()
            return JsonResponse({'success': True, 'message': f'Employee "{emp.name}" profile updated successfully!'})
        else:
            errors = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            return JsonResponse({'success': False, 'error': errors})

class EmployeeDetailView(LoginRequiredMixin, EngineerRequiredMixin, DetailView):
    model = Employee
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum, Case, When, Value, DecimalField
        from attendance.models import AttendanceStatus
        
        attendance_qs = self.object.attendance_records.all()
        days_worked = attendance_qs.aggregate(days=Sum(Case(
            When(status=AttendanceStatus.PRESENT, then=Value(1.0)),
            When(status=AttendanceStatus.LATE, then=Value(0.5)),
            default=Value(0.0),
            output_field=DecimalField(max_digits=5, decimal_places=1)
        )))["days"] or 0
        
        total_days = attendance_qs.count()
        if total_days > 0:
            present_or_late = attendance_qs.filter(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]).count()
            attendance_rate = round((present_or_late / total_days) * 100, 1)
        else:
            attendance_rate = 100.0
            
        payments = self.object.payments.order_by("-paid_on")
        total_paid = sum(p.amount for p in payments)
        
        context['attendance_rate'] = attendance_rate
        context['total_paid'] = total_paid
        context['days_worked'] = days_worked
        context['payments'] = payments
        return context

class EmployeeDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        employee = get_object_or_404(Employee, pk=pk)
        name = employee.name
        employee.is_archived = True
        employee.status = EmployeeStatus.INACTIVE
        employee.save(update_fields=["is_archived", "status"])
        return JsonResponse({'success': True, 'message': f'Employee "{name}" archived successfully!'})


class EmployeeUnarchiveView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        employee = get_object_or_404(Employee, pk=pk)
        name = employee.name
        employee.is_archived = False
        employee.status = EmployeeStatus.ACTIVE
        employee.save(update_fields=["is_archived", "status"])
        return JsonResponse({'success': True, 'message': f'Employee "{name}" restored successfully!'})
