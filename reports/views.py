from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.db.models import Sum, F, ExpressionWrapper
from django.db import models
from django.http import HttpResponse
import csv

from employees.models import Employee
from worksites.models import Worksite
from salaries.models import SalaryRecord
from payments.models import Payment
from materials.models import Material
from expenses.models import Expense


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "reports/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        salaries_total = SalaryRecord.objects.aggregate(total=Sum('net_salary'))['total'] or 0
        payments_total = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        materials_total = Material.objects.annotate(
            cost=ExpressionWrapper(F('quantity') * F('unit_price'), output_field=models.DecimalField(max_digits=15, decimal_places=2))
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        expenses_total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # If all totals are zero, fallback to dummy data to keep chart readable
        is_empty = (salaries_total == 0 and payments_total == 0 and materials_total == 0 and expenses_total == 0)
        
        if is_empty:
            salaries_val = 14500.00
            payments_val = 16390.00
            materials_val = 12565.00
            expenses_val = 3850.00
        else:
            salaries_val = float(salaries_total)
            payments_val = float(payments_total)
            materials_val = float(materials_total)
            expenses_val = float(expenses_total)
            
        context['report_stats'] = {
            'employees_count': Employee.objects.filter(is_archived=False).count(),
            'worksites_count': Worksite.objects.count(),
            'salaries_total': salaries_val,
            'payments_total': payments_val,
            'materials_total': materials_val,
            'expenses_total': expenses_val,
            'is_live_data': not is_empty,
        }
        return context


class EmployeeReportExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Role', 'Phone', 'Wage Rate', 'Worksite', 'Status', 'Joined Date'])
        
        employees = Employee.objects.all().select_related('worksite')
        for emp in employees:
            writer.writerow([
                emp.id,
                emp.name,
                emp.role,
                emp.phone,
                emp.wage,
                emp.worksite.name if emp.worksite else 'Unassigned',
                emp.status,
                emp.joined.strftime('%Y-%m-%d') if emp.joined else ''
            ])
        return response


class WorksiteReportExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="worksite_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Client', 'Location', 'Budget', 'Spend', 'Net Profit', 'Status', 'Progress (%)'])
        
        worksites = Worksite.objects.all()
        for ws in worksites:
            writer.writerow([
                ws.id,
                ws.name,
                ws.client,
                ws.location,
                ws.budget,
                ws.spend,
                ws.profit,
                ws.status,
                ws.progress
            ])
        return response


class FinancialReportExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Record Type', 'Detail / Name', 'Amount (Rs.)', 'Date / Period', 'Status'])
        
        salaries = SalaryRecord.objects.all().select_related('employee')
        for s in salaries:
            writer.writerow([
                'Salary Record',
                f"Salary for {s.employee.name}",
                s.net_salary,
                f"Week Ending {s.week_end_date}" if s.week_end_date else s.generated_at.strftime('%Y-%m-%d'),
                s.status
            ])
            
        payments = Payment.objects.all().select_related('employee')
        for p in payments:
            writer.writerow([
                'Payment Disbursed',
                f"Payment to {p.employee.name} ({p.get_method_display()})",
                p.amount,
                p.paid_on.strftime('%Y-%m-%d %H:%M'),
                'Completed'
            ])
            
        expenses = Expense.objects.all().select_related('worksite')
        for e in expenses:
            writer.writerow([
                'Expense',
                f"{e.category} - {e.description} (Worksite: {e.worksite.name})",
                e.amount,
                e.date.strftime('%Y-%m-%d'),
                e.status
            ])
            
        return response


class MaterialsReportExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="materials_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Worksite', 'Quantity', 'Unit', 'Unit Price', 'Total Cost', 'Supplier', 'Status'])
        
        materials = Material.objects.all().select_related('worksite')
        for m in materials:
            writer.writerow([
                m.id,
                m.name,
                m.worksite.name,
                m.quantity,
                m.unit,
                m.unit_price,
                m.total_cost,
                m.supplier,
                m.status
            ])
        return response


class SummaryReportExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="operation_summary.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Operational Summary Metric', 'Value'])
        
        writer.writerow(['Total Active Employees', Employee.objects.filter(is_archived=False).count()])
        writer.writerow(['Total Worksites', Worksite.objects.count()])
        
        salaries_sum = SalaryRecord.objects.aggregate(total=Sum('net_salary'))['total'] or 0
        payments_sum = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        expenses_sum = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        writer.writerow(['Total Salaries Generated (Rs.)', salaries_sum])
        writer.writerow(['Total Payments Disbursed (Rs.)', payments_sum])
        writer.writerow(['Total Operational Expenses (Rs.)', expenses_sum])
        
        return response
