from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
import datetime

from employees.models import Employee
from worksites.models import Worksite, WorksiteStatus
from payments.models import Payment
from expenses.models import Expense, ExpenseStatus


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Calculate stats
        payments_month_val = Payment.objects.filter(paid_on__year=now.year, paid_on__month=now.month).aggregate(total=Sum('amount'))['total'] or 0.00
        pending_expenses_val = Expense.objects.filter(status=ExpenseStatus.PENDING).aggregate(total=Sum('amount'))['total'] or 0.00
        
        context["stats"] = {
            "total_employees": Employee.objects.filter(is_archived=False).count(),
            "active_worksites": Worksite.objects.filter(status=WorksiteStatus.ACTIVE).count(),
            "payments_month": float(payments_month_val),
            "pending_expenses": float(pending_expenses_val),
        }
        
        # 1. Worksite distribution for Doughnut Chart
        active_count = Worksite.objects.filter(status=WorksiteStatus.ACTIVE).count()
        on_hold_count = Worksite.objects.filter(status=WorksiteStatus.ON_HOLD).count()
        completed_count = Worksite.objects.filter(status=WorksiteStatus.COMPLETED).count()
        context["worksite_status_counts"] = [active_count, on_hold_count, completed_count]
        
        # 2. Monthly Expenses data for Line Chart
        months_labels = []
        months_data = []
        today = datetime.date.today()
        for i in range(5, -1, -1):
            d = today - datetime.timedelta(days=i*30)
            months_labels.append(d.strftime("%b"))
            sum_val = Expense.objects.filter(date__year=d.year, date__month=d.month).aggregate(total=Sum('amount'))['total'] or 0
            months_data.append(float(sum_val))
            
        # Fallback to visual placeholder trend if there is no data in DB yet
        if sum(months_data) == 0:
            months_labels = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"]
            months_data = [12000, 18500, 24000, 15000, 29000, 38500]
            
        context["chart_labels"] = months_labels
        context["chart_data"] = months_data

        # 3. Build live recent operational activities
        activities = []
        
        # Add Recent Employees
        recent_employees = Employee.objects.filter(is_archived=False).select_related("worksite").order_by("-id")[:5]
        for emp in recent_employees:
            activities.append({
                "icon": "bi-person-plus text-primary",
                "title": f"Registered employee: {emp.name}",
                "worksite": emp.worksite.name if emp.worksite else "Unassigned",
                "user": "System Admin",
                "status": "Success",
                "date": emp.joined.strftime("%b %d, %Y") if emp.joined else "-",
                "timestamp": timezone.make_aware(timezone.datetime.combine(emp.joined, timezone.datetime.min.time())) if emp.joined else now
            })
            
        # Add Recent Expenses
        recent_expenses = Expense.objects.select_related("worksite").order_by("-id")[:5]
        for exp in recent_expenses:
            activities.append({
                "icon": "bi-cash-coin text-warning",
                "title": f"Logged expense: {exp.category} (₹{exp.amount})",
                "worksite": exp.worksite.name if exp.worksite else "-",
                "user": "Supervisor",
                "status": exp.status,
                "date": exp.date.strftime("%b %d, %Y"),
                "timestamp": timezone.make_aware(timezone.datetime.combine(exp.date, timezone.datetime.min.time())) if exp.date else now
            })
            
        # Add Recent Worksites
        recent_worksites = Worksite.objects.order_by("-id")[:5]
        for site in recent_worksites:
            activities.append({
                "icon": "bi-geo-alt text-success",
                "title": f"Created worksite: {site.name}",
                "worksite": site.name,
                "user": "Project Engineer",
                "status": "Completed" if site.status == WorksiteStatus.COMPLETED else "Pending" if site.status == WorksiteStatus.ON_HOLD else "Success",
                "date": site.start_date.strftime("%b %d, %Y") if site.start_date else "-",
                "timestamp": timezone.make_aware(timezone.datetime.combine(site.start_date, timezone.datetime.min.time())) if site.start_date else now
            })
            
        # Sort activities by timestamp descending
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        context["activities"] = activities[:6]
        
        return context
