from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
import datetime

from employees.models import Employee
from worksites.models import Worksite, WorksiteStatus, DailySiteLog, ClientPayment
from payments.models import Payment
from expenses.models import Expense, ExpenseStatus


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        worksites = Worksite.objects.all()
        active_worksites_qs = worksites.filter(status=WorksiteStatus.ACTIVE)
        
        payments_month_val = Payment.objects.filter(paid_on__year=now.year, paid_on__month=now.month).aggregate(total=Sum('amount'))['total'] or 0.00
        pending_expenses_val = Expense.objects.filter(status=ExpenseStatus.PENDING).aggregate(total=Sum('amount'))['total'] or 0.00
        
        total_budget = sum(w.budget for w in worksites)
        total_paid = sum(w.client_paid for w in worksites)
        total_balance = sum(w.client_balance for w in worksites)
        total_spend = sum(w.total_spend for w in worksites)
        
        context["stats"] = {
            "total_employees": Employee.objects.filter(is_archived=False).count(),
            "active_worksites": active_worksites_qs.count(),
            "total_worksites": worksites.count(),
            "payments_month": float(payments_month_val),
            "pending_expenses": float(pending_expenses_val),
            "total_budget": float(total_budget),
            "total_paid": float(total_paid),
            "total_balance": float(total_balance),
            "total_spend": float(total_spend),
        }
        
        # 1. Worksite distribution for Doughnut Chart
        active_count = active_worksites_qs.count()
        on_hold_count = worksites.filter(status=WorksiteStatus.ON_HOLD).count()
        completed_count = worksites.filter(status=WorksiteStatus.COMPLETED).count()
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
            
        if sum(months_data) == 0:
            months_labels = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"]
            months_data = [12000, 18500, 24000, 15000, 29000, 38500]
            
        context["chart_labels"] = months_labels
        context["chart_data"] = months_data

        # 3. Active worksites list with progress
        context["active_worksites_list"] = active_worksites_qs.order_by("-id")[:4]
        
        # 4. Recent Daily Site Logs
        context["recent_site_logs"] = DailySiteLog.objects.select_related("worksite", "logged_by").order_by("-date", "-created_at")[:4]

        # 5. Build live recent operational activities
        activities = []
        
        recent_employees = Employee.objects.filter(is_archived=False).select_related("worksite").order_by("-id")[:4]
        for emp in recent_employees:
            activities.append({
                "icon": "bi-person-plus text-primary",
                "title": f"Registered employee: {emp.name}",
                "worksite": emp.worksite.name if emp.worksite else "Unassigned",
                "user": "System Admin",
                "status": "Success",
                "time": emp.joined.strftime("%b %d") if emp.joined else "-",
                "timestamp": timezone.make_aware(timezone.datetime.combine(emp.joined, timezone.datetime.min.time())) if emp.joined else now
            })
            
        recent_expenses = Expense.objects.select_related("worksite").order_by("-id")[:4]
        for exp in recent_expenses:
            activities.append({
                "icon": "bi-receipt text-danger",
                "title": f"Logged expense: {exp.category} (₹{exp.amount:,.2f})",
                "worksite": exp.worksite.name if exp.worksite else "-",
                "user": "Supervisor",
                "status": exp.status,
                "time": exp.date.strftime("%b %d"),
                "timestamp": timezone.make_aware(timezone.datetime.combine(exp.date, timezone.datetime.min.time())) if exp.date else now
            })
            
        recent_payments = ClientPayment.objects.select_related("worksite").order_by("-id")[:4]
        for pay in recent_payments:
            activities.append({
                "icon": "bi-cash-stack text-success",
                "title": f"Client payment: {pay.milestone} (₹{pay.amount:,.2f})",
                "worksite": pay.worksite.name,
                "user": pay.logged_by.username if pay.logged_by else "Client Billing",
                "status": "Approved",
                "time": pay.payment_date.strftime("%b %d"),
                "timestamp": timezone.make_aware(timezone.datetime.combine(pay.payment_date, timezone.datetime.min.time())) if pay.payment_date else now
            })

        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        context["activities"] = activities[:6]
        
        return context
