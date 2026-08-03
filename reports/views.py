from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.db.models import Sum, F, ExpressionWrapper
from django.db import models
from django.http import HttpResponse

from accounts.mixins import EngineerRequiredMixin
from employees.models import Employee
from worksites.models import Worksite
from salaries.models import SalaryRecord
from payments.models import Payment
from materials.models import Material
from expenses.models import Expense
from .pdf_generator import generate_pdf_report, generate_monthly_attendance_pdf


class ReportsView(LoginRequiredMixin, EngineerRequiredMixin, TemplateView):
    template_name = "reports/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        salaries_total = SalaryRecord.objects.aggregate(total=Sum('net_salary'))['total'] or 0
        payments_total = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        materials_total = Material.objects.annotate(
            cost=ExpressionWrapper(F('quantity') * F('unit_price'), output_field=models.DecimalField(max_digits=15, decimal_places=2))
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        expenses_total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
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
        context['worksites'] = Worksite.objects.order_by("name")
        return context


class EmployeeReportExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        employees = Employee.objects.all().select_related('worksite')
        active_count = employees.filter(is_archived=False).count()
        total_wages = sum(e.wage for e in employees if e.wage)
        
        summary_cards = [
            ("Total Registered", f"{employees.count()} Workers"),
            ("Active Workforce", f"{active_count} Workers"),
            ("Est. Daily Wages", f"Rs. {total_wages:,.2f}")
        ]
        
        table_headers = ["ID", "Name", "Role", "Phone", "Wage Rate", "Worksite", "Status"]
        table_data = []
        for emp in employees:
            table_data.append([
                f"#{emp.id}",
                emp.name,
                emp.role,
                emp.phone,
                f"Rs. {emp.wage:,.2f}" if emp.wage else "Rs. 0.00",
                emp.worksite.name if emp.worksite else "Unassigned",
                emp.status.capitalize() if emp.status else "Active"
            ])
            
        pdf = generate_pdf_report(
            title="Workforce & Employee Directory Report",
            subtitle="Complete active roster, daily wage rates, contact phone numbers, and worksite assignments.",
            summary_cards=summary_cards,
            table_headers=table_headers,
            table_data=table_data,
            col_widths=[0.6, 1.4, 1.1, 1.1, 1.1, 1.3, 0.9]
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Employee_Report.pdf"'
        return response


class WorksiteReportExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        worksites = Worksite.objects.all()
        total_budget = sum(w.budget for w in worksites)
        total_paid = sum(w.client_paid for w in worksites)
        total_balance = sum(w.client_balance for w in worksites)
        
        summary_cards = [
            ("Total Worksites", f"{worksites.count()} Sites"),
            ("Total Project Value", f"Rs. {total_budget:,.2f}"),
            ("Client Paid", f"Rs. {total_paid:,.2f}"),
            ("Balance Due", f"Rs. {total_balance:,.2f}")
        ]
        
        table_headers = ["ID", "Site Name", "Client", "Location", "Budget", "Spend", "Paid", "Balance", "Progress"]
        table_data = []
        for ws in worksites:
            table_data.append([
                f"#{ws.id}",
                ws.name,
                ws.client,
                ws.location,
                f"Rs. {ws.budget:,.2f}",
                f"Rs. {ws.spend:,.2f}",
                f"Rs. {ws.client_paid:,.2f}",
                f"Rs. {ws.client_balance:,.2f}",
                f"{ws.progress}%"
            ])
            
        pdf = generate_pdf_report(
            title="Worksites Performance & Receivables Report",
            subtitle="Project valuations, client billing progress, spendings, and completion milestones.",
            summary_cards=summary_cards,
            table_headers=table_headers,
            table_data=table_data,
            col_widths=[0.5, 1.2, 1.0, 1.0, 0.9, 0.9, 0.8, 0.8, 0.4]
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Worksite_Report.pdf"'
        return response


class FinancialReportExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        salaries = SalaryRecord.objects.all().select_related('employee')
        payments = Payment.objects.all().select_related('employee')
        expenses = Expense.objects.all().select_related('worksite')
        
        total_salaries = sum(s.net_salary for s in salaries)
        total_payments = sum(p.amount for p in payments)
        total_expenses = sum(e.amount for e in expenses)
        
        summary_cards = [
            ("Salaries Generated", f"Rs. {total_salaries:,.2f}"),
            ("Payments Disbursed", f"Rs. {total_payments:,.2f}"),
            ("Site Expenses", f"Rs. {total_expenses:,.2f}")
        ]
        
        table_headers = ["Type", "Description / Details", "Amount", "Date / Period", "Status"]
        table_data = []
        
        for s in salaries:
            table_data.append([
                "Salary Record",
                f"Payroll for {s.employee.name}",
                f"Rs. {s.net_salary:,.2f}",
                f"Week Ending {s.week_end_date}" if s.week_end_date else s.generated_at.strftime('%Y-%m-%d'),
                s.status.capitalize() if hasattr(s, 'status') else "Completed"
            ])
            
        for p in payments:
            table_data.append([
                "Payment",
                f"Disbursement to {p.employee.name} ({p.get_method_display()})",
                f"Rs. {p.amount:,.2f}",
                p.paid_on.strftime('%Y-%m-%d %H:%M'),
                "Completed"
            ])
            
        for e in expenses:
            table_data.append([
                "Expense",
                f"{e.category} - {e.description} ({e.worksite.name if e.worksite else 'General'})",
                f"Rs. {e.amount:,.2f}",
                e.date.strftime('%Y-%m-%d'),
                e.status.capitalize() if hasattr(e, 'status') else "Approved"
            ])
            
        pdf = generate_pdf_report(
            title="Financial Ledger & Disbursement Audit Report",
            subtitle="Detailed record of payroll distributions, payment receipts, and operational expenses.",
            summary_cards=summary_cards,
            table_headers=table_headers,
            table_data=table_data,
            col_widths=[1.1, 2.5, 1.2, 1.5, 1.2]
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Financial_Ledger.pdf"'
        return response


class MaterialsReportExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        materials = Material.objects.all().select_related('worksite')
        total_cost = sum(m.total_cost for m in materials)
        delivered_count = materials.filter(status='Delivered').count()
        
        summary_cards = [
            ("Total Stock Items", f"{materials.count()} Items"),
            ("Total Procurement Cost", f"Rs. {total_cost:,.2f}"),
            ("Delivered Stock", f"{delivered_count} Items")
        ]
        
        table_headers = ["ID", "Material Name", "Worksite", "Qty / Stock", "Unit Cost", "Total Cost", "Supplier", "Status"]
        table_data = []
        for m in materials:
            table_data.append([
                f"#{m.id}",
                m.name,
                m.worksite.name if m.worksite else "N/A",
                f"{m.quantity} {m.unit}",
                f"Rs. {m.unit_price:,.2f}",
                f"Rs. {m.total_cost:,.2f}",
                m.supplier if m.supplier else "N/A",
                m.status
            ])
            
        pdf = generate_pdf_report(
            title="Onsite Materials Inventory Report",
            subtitle="Raw construction material stock counts, unit valuations, site allocations, and supplier logs.",
            summary_cards=summary_cards,
            table_headers=table_headers,
            table_data=table_data,
            col_widths=[0.6, 1.4, 1.2, 1.0, 1.0, 1.0, 0.7, 0.6]
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Materials_Report.pdf"'
        return response


class SummaryReportExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        emp_count = Employee.objects.filter(is_archived=False).count()
        site_count = Worksite.objects.count()
        
        salaries_sum = SalaryRecord.objects.aggregate(total=Sum('net_salary'))['total'] or 0
        payments_sum = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        expenses_sum = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        materials_sum = Material.objects.annotate(
            cost=ExpressionWrapper(F('quantity') * F('unit_price'), output_field=models.DecimalField(max_digits=15, decimal_places=2))
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        summary_cards = [
            ("Active Workforce", f"{emp_count} Employees"),
            ("Active Worksites", f"{site_count} Worksites"),
            ("Total Operation Costs", f"Rs. {(salaries_sum + expenses_sum + materials_sum):,.2f}")
        ]
        
        table_headers = ["Operational Audit Metric", "Category", "Recorded Value / Amount", "System Status"]
        table_data = [
            ["Total Active Workforce Headcount", "HR & Staffing", f"{emp_count} Workers", "Active"],
            ["Registered Construction Sites", "Project Mgmt", f"{site_count} Sites", "Active"],
            ["Total Salaries Generated", "Payroll Ledger", f"Rs. {salaries_sum:,.2f}", "Calculated"],
            ["Total Payments Disbursed", "Disbursements", f"Rs. {payments_sum:,.2f}", "Completed"],
            ["Total Materials Inventory Spend", "Procurement", f"Rs. {materials_sum:,.2f}", "Audited"],
            ["Total Operational Site Expenses", "Expenses", f"Rs. {expenses_sum:,.2f}", "Recorded"],
        ]
        
        pdf = generate_pdf_report(
            title="Decore Construction Operational Executive Summary",
            subtitle="Comprehensive high-level operational overview across workforce, worksites, and aggregate ledger totals.",
            summary_cards=summary_cards,
            table_headers=table_headers,
            table_data=table_data,
            col_widths=[2.5, 1.5, 2.0, 1.5]
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Operation_Summary.pdf"'
        return response


class MonthlyAttendanceExportView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from datetime import datetime
        now = datetime.now()
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        worksite_id = request.GET.get('worksite')

        pdf = generate_monthly_attendance_pdf(year, month, worksite_id)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Attendance_Roster_{month}_{year}.pdf"'
        return response
