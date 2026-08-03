from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from django.utils import timezone

from employees.models import Employee
from worksites.models import Worksite, WorksiteStatus, ClientPayment
from attendance.models import Attendance, AttendanceStatus
from materials.models import Material
from expenses.models import Expense, ExpenseStatus
from salaries.models import SalaryRecord, SalaryStatus


def make_dt(d, default_now=None):
    if not d:
        return default_now or timezone.now()
    dt = timezone.datetime.combine(d, timezone.datetime.min.time())
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = timezone.localdate()

        worksites = list(Worksite.objects.prefetch_related("materials", "attendance_records__employee").all())
        active_worksites_qs = Worksite.objects.filter(status=WorksiteStatus.ACTIVE)
        total_employees = Employee.objects.filter(is_archived=False)

        # 1. Quick Statistics (6 Key Cards)
        active_worksites_cnt = active_worksites_qs.count()
        total_employees_cnt = total_employees.count()

        # Present Today
        today_attendance = Attendance.objects.filter(date=today)
        present_today_cnt = today_attendance.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.OVERTIME, 'present', 'late', 'overtime']
        ).count()
        
        absent_today_cnt = today_attendance.filter(
            status__in=[AttendanceStatus.ABSENT, 'absent']
        ).count()

        today_summary_marked = today_attendance.exists()

        total_revenue = sum((w.budget for w in worksites), Decimal("0.00"))
        exp_sum = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
        total_expenses = sum((w.total_spend for w in worksites), Decimal("0.00")) + exp_sum
        net_profit = total_revenue - total_expenses

        context["stats"] = {
            "active_worksites": active_worksites_cnt,
            "total_employees": total_employees_cnt,
            "present_today": present_today_cnt,
            "total_revenue": float(total_revenue),
            "total_expenses": float(total_expenses),
            "net_profit": float(net_profit),
            "net_profit_abs": abs(float(net_profit)),
            "is_profit_positive": net_profit >= 0,
        }

        # 2. Today's Summary
        today_income_val = ClientPayment.objects.filter(payment_date=today).aggregate(total=Sum('amount'))['total'] or Decimal("0.00")
        today_expenses_val = Expense.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or Decimal("0.00")

        context["today_summary"] = {
            "present_workers": present_today_cnt,
            "absent_workers": absent_today_cnt if today_summary_marked else 0,
            "today_income": float(today_income_val),
            "today_expenses": float(today_expenses_val),
            "marked": today_summary_marked
        }

        # 3. Active Worksites (Top 3 latest)
        context["latest_active_worksites"] = active_worksites_qs.order_by("-id")[:3]

        # 4. Recent Activity (Latest 5 items across system)
        activities = []

        # Attendance Marked
        recent_att = Attendance.objects.select_related("employee", "worksite").order_by("-date", "-id")[:2]
        for att in recent_att:
            activities.append({
                "icon": "bi-calendar-check text-success",
                "title": f"Marked attendance: {att.employee.name} ({att.get_status_display()})",
                "subtitle": att.worksite.name if att.worksite else "General Site",
                "time": att.date.strftime("%b %d") if att.date else "-",
                "timestamp": make_dt(att.date, now)
            })

        # Expenses Recorded
        recent_expenses = Expense.objects.select_related("worksite").order_by("-id")[:2]
        for exp in recent_expenses:
            activities.append({
                "icon": "bi-receipt text-danger",
                "title": f"Expense recorded: {exp.category} (₹{exp.amount:,.2f})",
                "subtitle": exp.worksite.name if exp.worksite else "General",
                "time": exp.date.strftime("%b %d") if exp.date else "-",
                "timestamp": make_dt(exp.date, now)
            })

        # Materials Added
        recent_mats = Material.objects.select_related("worksite").order_by("-id")[:2]
        for mat in recent_mats:
            activities.append({
                "icon": "bi-boxes text-primary",
                "title": f"Material added: {mat.name} ({mat.quantity} {mat.unit})",
                "subtitle": mat.worksite.name if mat.worksite else "General Stock",
                "time": "Recent",
                "timestamp": now
            })

        # Salaries Paid
        recent_sal = SalaryRecord.objects.select_related("employee").filter(status=SalaryStatus.COMPLETED).order_by("-paid_at", "-id")[:2]
        for sal in recent_sal:
            activities.append({
                "icon": "bi-cash-stack text-info",
                "title": f"Salary paid: {sal.employee.name} (₹{sal.net_salary:,.2f})",
                "subtitle": f"Week ending {sal.week_end_date.strftime('%b %d')}" if sal.week_end_date else "Weekly",
                "time": sal.paid_at.strftime("%b %d") if sal.paid_at else "Recent",
                "timestamp": sal.paid_at if sal.paid_at else now
            })

        # Client Payment
        recent_payments = ClientPayment.objects.select_related("worksite").order_by("-id")[:2]
        for pay in recent_payments:
            activities.append({
                "icon": "bi-wallet2 text-success",
                "title": f"Client payment: {pay.milestone} (₹{pay.amount:,.2f})",
                "subtitle": pay.worksite.name,
                "time": pay.payment_date.strftime("%b %d") if pay.payment_date else "-",
                "timestamp": make_dt(pay.payment_date, now)
            })

        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        context["recent_activities"] = activities[:5]

        # 5. Smart Operational Alerts
        alerts = []

        # Alert A: High Client Receivables Balance
        total_balance_val = sum((w.client_balance for w in worksites if w.client_balance > 0), Decimal("0.00"))
        if total_balance_val > 0:
            alerts.append({
                "type": "warning",
                "icon": "bi-exclamation-triangle-fill text-warning",
                "title": f"Pending Client Receivables: ₹{total_balance_val:,.2f}",
                "description": "Outstanding client milestone payments due across active construction sites.",
                "action_url": "/worksites/",
                "action_text": "View Receivables"
            })

        # Alert B: Low Material Stock
        low_mats = Material.objects.filter(quantity__lte=5)
        if low_mats.exists():
            count_low = low_mats.count()
            first_mat = low_mats.first()
            alerts.append({
                "type": "danger",
                "icon": "bi-box-seam-fill text-danger",
                "title": f"Low Stock Alert: {count_low} Material(s)",
                "description": f"Item '{first_mat.name}' is running low ({first_mat.quantity} {first_mat.unit} remaining).",
                "action_url": "/materials/",
                "action_text": "Reorder Stock"
            })

        # Alert C: Pending Expense Approvals
        pending_exp_cnt = Expense.objects.filter(status=ExpenseStatus.PENDING).count()
        if pending_exp_cnt > 0:
            alerts.append({
                "type": "info",
                "icon": "bi-receipt text-info",
                "title": f"{pending_exp_cnt} Expense(s) Awaiting Approval",
                "description": "Supervisor site outgoings require executive approval.",
                "action_url": "/expenses/",
                "action_text": "Review Expenses"
            })

        # Alert D: Pending Weekly Payroll
        pending_payroll_cnt = SalaryRecord.objects.filter(status=SalaryStatus.PENDING).count()
        if pending_payroll_cnt > 0:
            alerts.append({
                "type": "primary",
                "icon": "bi-cash-stack text-primary",
                "title": f"{pending_payroll_cnt} Weekly Pay Slips Unpaid",
                "description": "Finalized weekly worker payroll balances are ready for payment.",
                "action_url": "/salaries/",
                "action_text": "Process Payroll"
            })

        context["alerts"] = alerts
        return context
