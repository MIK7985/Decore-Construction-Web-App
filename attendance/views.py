from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, View

from accounts.mixins import EngineerRequiredMixin
from employees.models import Employee
from worksites.models import Worksite
from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ("employee", "worksite", "date", "status", "notes")

    def clean(self):
        cleaned = super().clean()
        employee = cleaned.get("employee")
        worksite = cleaned.get("worksite")
        if employee and worksite and employee.worksite_id and employee.worksite_id != worksite.id:
            self.add_error("worksite", "Select the employee's assigned worksite or leave it blank.")
        return cleaned


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = "attendance/attendance_list.html"
    context_object_name = "attendance_records"

    def get_queryset(self):
        qs = Attendance.objects.select_related("employee", "worksite")
        date_filter = self.request.GET.get('date')
        if not date_filter:
            date_filter = timezone.localdate().isoformat()
        qs = qs.filter(date=date_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate().isoformat()
        context["today_date"] = today
        context["filter_date"] = self.request.GET.get('date', today)
        context["employees"] = Employee.objects.filter(is_archived=False).select_related("worksite").order_by("name")
        context["worksites"] = Worksite.objects.order_by("name")
        return context


class AttendanceCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = AttendanceForm(request.POST)
        if form.is_valid():
            record = form.save()
            return JsonResponse({"success": True, "message": f"Attendance for {record.employee.name} saved successfully."})
        return JsonResponse({"success": False, "error": form.errors.as_text()}, status=400)


class AttendanceUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        record = get_object_or_404(Attendance, pk=pk)
        form = AttendanceForm(request.POST, instance=record)
        if form.is_valid():
            record = form.save()
            return JsonResponse({"success": True, "message": f"Attendance for {record.employee.name} updated successfully."})
        return JsonResponse({"success": False, "error": form.errors.as_text()}, status=400)

from django.shortcuts import render
from django.db import transaction
import json

class AttendanceSheetView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        if not date_str:
            date_str = timezone.localdate().isoformat()
        
        employees = (
            Employee.objects
            .filter(is_archived=False)
            .select_related("worksite")
            .only("id", "name", "role", "worksite_id", "worksite__name")
            .order_by("name")
        )
        worksites = Worksite.objects.only("id", "name").order_by("name")
        
        attendance_records = (
            Attendance.objects
            .filter(date=date_str)
            .select_related("employee")
            .only("id", "employee_id", "worksite_id", "status", "notes")
        )
        saved_dict = {r.employee_id: r for r in attendance_records}
        
        sheet_records = []
        for emp in employees:
            saved = saved_dict.get(emp.id)
            sheet_records.append({
                'employee': emp,
                'status': saved.status if saved else 'present',
                'notes': saved.notes if saved else '',
                'worksite_id': saved.worksite_id if saved else (emp.worksite_id or '')
            })

        context = {
            'selected_date': date_str,
            'sheet_records': sheet_records,
            'worksites': worksites,
            'today_date': timezone.localdate().isoformat()
        }
        return render(request, "attendance/attendance_sheet.html", context)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            records = data.get('records', [])
            
            if not date_str:
                return JsonResponse({'success': False, 'error': 'Date is required.'}, status=400)

            with transaction.atomic():
                for item in records:
                    emp_id = item.get('employee_id')
                    status = item.get('status')
                    notes = item.get('notes', '')
                    worksite_id = item.get('worksite_id') or None
                    
                    if not emp_id or not status:
                        continue

                    emp = Employee.objects.get(id=emp_id)
                    if not worksite_id and emp.worksite_id:
                        worksite_id = emp.worksite_id

                    Attendance.objects.update_or_create(
                        employee_id=emp_id,
                        date=date_str,
                        defaults={
                            'status': status,
                            'notes': notes,
                            'worksite_id': worksite_id
                        }
                    )
            return JsonResponse({'success': True, 'message': 'Daily attendance sheet saved successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

