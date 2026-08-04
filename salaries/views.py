import datetime
from decimal import Decimal
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db import models
from django.db.models import Case, DecimalField, Prefetch, Sum, Value, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.mixins import EngineerRequiredMixin
from attendance.models import Attendance, AttendanceStatus
from employees.models import Employee
from payments.models import Payment
from .models import SalaryRecord, SalaryStatus
import hashlib
from django.conf import settings

def get_salary_receipt_token(salary_pk):
    return hashlib.sha256(f"receipt-{salary_pk}-{settings.SECRET_KEY}".encode()).hexdigest()[:16]



def get_saturday_for_date(d):
    """Given any date d, return the Saturday at the end of that week (Sunday-Saturday)."""
    if d.weekday() == 5:
        return d
    elif d.weekday() == 6:
        return d + datetime.timedelta(days=6)
    else:
        return d + datetime.timedelta(days=(5 - d.weekday()))


def parse_week_period(period_str):
    """
    Parse a period string like '2026-08-01' or '2026-W31'.
    Returns (start_date, sat_date).
    """
    today = timezone.localdate()
    if period_str:
        try:
            sat_date = datetime.datetime.strptime(period_str, "%Y-%m-%d").date()
            sat_date = get_saturday_for_date(sat_date)
        except ValueError:
            sat_date = get_saturday_for_date(today)
    else:
        sat_date = get_saturday_for_date(today)

    start_date = sat_date - datetime.timedelta(days=6)
    return start_date, sat_date


def get_recent_months(count=12):
    """Generate a list of recent months (YYYY-MM) for the dropdown."""
    today = timezone.localdate()
    months = []
    for i in range(count):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        val = f"{y:04d}-{m:02d}"
        label = timezone.datetime(y, m, 1).strftime("%B %Y")
        months.append({
            'val': val,
            'label': label,
            'year': y,
            'month': m
        })
    return months


def get_weeks_grouped_by_month(count_weeks=52):
    """Generate Saturday week endings grouped by their YYYY-MM month key."""
    today = timezone.localdate()
    current_sat = get_saturday_for_date(today)
    grouped = {}
    for i in range(count_weeks):
        sat = current_sat - datetime.timedelta(weeks=i)
        sun = sat - datetime.timedelta(days=6)
        
        # Add to primary month key
        month_key = f"{sat.year:04d}-{sat.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = []
        grouped[month_key].append((sat, sun))
        
        # If Saturday date is <= 5, it means the week started in the previous month.
        if sat.day <= 5:
            prev_m = sat.month - 1
            prev_y = sat.year
            if prev_m == 0:
                prev_m = 12
                prev_y -= 1
            prev_month_key = f"{prev_y:04d}-{prev_m:02d}"
            if prev_month_key not in grouped:
                grouped[prev_month_key] = []
            grouped[prev_month_key].append((sat, sun))
            
    final_grouped = {}
    for month_key, weeks in grouped.items():
        weeks.sort(key=lambda w: w[0])
        final_grouped[month_key] = []
        for idx, (sat, sun) in enumerate(weeks):
            week_num = idx + 1
            label = f"Week {week_num} ({sun.strftime('%b %d')} - {sat.strftime('%b %d')})"
            final_grouped[month_key].append({
                'val': sat.strftime('%Y-%m-%d'),
                'label': label
            })
    return final_grouped


def payroll_preview(start_date, end_date):
    """Calculate a 7-day week in memory (Sunday to Saturday); does not create records."""
    rows = []
    existing = {
        record.employee_id: record 
        for record in SalaryRecord.objects.filter(week_end_date=end_date).select_related("employee").prefetch_related("payments")
    }
    # Batch-fetch all employees with their attendance for the week in one query
    employees = (
        Employee.objects
        .filter(is_archived=False)
        .prefetch_related(
            models.Prefetch(
                'attendance_records',
                queryset=Attendance.objects.filter(
                    date__gte=start_date, date__lte=end_date
                ).only('employee_id', 'status'),
                to_attr='week_attendance'
            )
        )
        .order_by("name")
    )
    for employee in employees:
        # Use prefetched week_attendance instead of triggering separate query per employee
        attendance_statuses = [a.status for a in employee.week_attendance]
        paid_days = sum(
            Decimal("1.0") if s == AttendanceStatus.PRESENT else
            Decimal("0.5") if s == AttendanceStatus.LATE else
            Decimal("1.5") if s == AttendanceStatus.OVERTIME else
            Decimal("0.0")
            for s in attendance_statuses
        )
        
        record = existing.get(employee.id)
        if paid_days == 0 and not record:
            continue
            
        daily_wage = record.daily_wage if record else employee.wage
        bonus = record.bonus if record else Decimal("0.00")
        deductions = record.deductions if record else Decimal("0.00")
        net_salary = (daily_wage * paid_days) + bonus - deductions
        
        paid_amount = sum(p.amount for p in record.payments.all()) if record else Decimal("0.00")
        unpaid_balance = net_salary - paid_amount
        
        status = record.status if record else "preview"
        if record and status == SalaryStatus.COMPLETED and unpaid_balance > 0:
            status = SalaryStatus.PENDING

        rows.append(SimpleNamespace(
            employee=employee, start_date=start_date, end_date=end_date, daily_wage=daily_wage,
            present_days=paid_days, bonus=bonus, deductions=deductions,
            net_salary=net_salary, paid_amount=paid_amount, unpaid_balance=unpaid_balance,
            status=status, record=record,
        ))
    return rows


class SalaryListView(LoginRequiredMixin, TemplateView):
    template_name = "salaries/salary_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.request.GET.get("period") or ""
        start_date, end_date = parse_week_period(period)
        salaries = payroll_preview(start_date, end_date)
        context["salaries"] = salaries
        context["selected_period"] = end_date.strftime("%Y-%m-%d")
        context["selected_month"] = f"{end_date.year:04d}-{end_date.month:02d}"
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["recent_months"] = get_recent_months()
        context["weeks_grouped"] = get_weeks_grouped_by_month()
        context["totals"] = {
            "net_salary": sum((row.net_salary for row in salaries), Decimal("0.00")),
            "paid": sum((row.paid_amount for row in salaries), Decimal("0.00")),
            "pending": sum((row.unpaid_balance for row in salaries if row.unpaid_balance > 0), Decimal("0.00")),
        }
        return context


class SalaryGenerateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        period = request.POST.get("period", "")
        start_date, end_date = parse_week_period(period)
        created = 0
        updated = 0
        for row in payroll_preview(start_date, end_date):
            if row.record and row.record.status == SalaryStatus.COMPLETED:
                continue
            if row.record:
                row.record.daily_wage = row.daily_wage
                row.record.present_days = row.present_days
                row.record.bonus = row.bonus
                row.record.deductions = row.deductions
                row.record.save()
                updated += 1
            else:
                SalaryRecord.objects.create(
                    employee=row.employee, week_end_date=end_date, daily_wage=row.daily_wage,
                    present_days=row.present_days, bonus=row.bonus, deductions=row.deductions,
                    net_salary=row.net_salary,
                )
                created += 1
        messages.success(request, f"Finalized {created} new and refreshed {updated} pending weekly salary record(s) for week ending {end_date.strftime('%b %d, %Y')}.")
        return redirect(f"{reverse('salaries:list')}?period={end_date.strftime('%Y-%m-%d')}")


class SalaryPayView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        employee_id = request.POST.get("employee_id")
        period = request.POST.get("period", "")
        start_date, end_date = parse_week_period(period)

        method = request.POST.get("method", Payment.Method.BANK_TRANSFER)
        reference_number = request.POST.get("reference_number", "").strip()

        with transaction.atomic():
            employee = get_object_or_404(Employee, id=employee_id)
            
            salary, created = SalaryRecord.objects.select_for_update().get_or_create(
                employee=employee,
                week_end_date=end_date,
                defaults={
                    'daily_wage': employee.wage,
                    'present_days': Decimal("0.0"),
                    'bonus': Decimal("0.00"),
                    'deductions': Decimal("0.00"),
                    'net_salary': Decimal("0.00"),
                    'status': SalaryStatus.PENDING
                }
            )

            paid_amount = sum(p.amount for p in salary.payments.all())

            attendance = employee.attendance_records.filter(date__gte=start_date, date__lte=end_date)
            paid_days = attendance.aggregate(days=Sum(Case(
                When(status=AttendanceStatus.PRESENT, then=Value(Decimal("1.0"))),
                When(status=AttendanceStatus.LATE, then=Value(Decimal("0.5"))),
                When(status=AttendanceStatus.OVERTIME, then=Value(Decimal("1.5"))),
                default=Value(Decimal("0.0")),
                output_field=DecimalField(max_digits=5, decimal_places=1),
            )))["days"] or Decimal("0.0")

            salary.present_days = paid_days
            if created:
                salary.daily_wage = employee.wage
            salary.recalculate()
            
            unpaid_balance = salary.net_salary - paid_amount
            if unpaid_balance <= 0:
                if salary.status != SalaryStatus.COMPLETED:
                    salary.status = SalaryStatus.COMPLETED
                    salary.save(update_fields=["status"])
                messages.info(request, f"Weekly salary for {employee.name} is already fully paid.")
                return redirect(f"{reverse('salaries:list')}?period={end_date.strftime('%Y-%m-%d')}")

            Payment.objects.create(
                salary=salary,
                employee=employee,
                amount=unpaid_balance,
                method=method,
                reference_number=reference_number,
            )

            salary.status = SalaryStatus.COMPLETED
            salary.paid_at = timezone.now()
            salary.save()
            
            import re
            import urllib.parse
            clean_phone = re.sub(r"\D", "", employee.phone)
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
            
            token = get_salary_receipt_token(salary.pk)
            pdf_url = request.build_absolute_uri(reverse('salaries:receipt_pdf', kwargs={'pk': salary.pk})) + f"?token={token}"
            week_range_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            
            # Simple, clean, professional WhatsApp receipt message
            whatsapp_msg = (
                f"📄 *SALARY PAYMENT RECEIPT VOUCHER*\n\n"
                f"Dear *{employee.name}*,\n"
                f"Your weekly salary payment of *₹{unpaid_balance:,.2f}* for period *{week_range_str}* has been processed successfully.\n\n"
                f"💰 *Payment Summary:*\n"
                f"• Days Worked: {salary.present_days} Days\n"
                f"• Net Amount Paid: *₹{unpaid_balance:,.2f}*\n"
                f"• Payment Method: {method.replace('_', ' ').title()}\n"
                f"• Reference ID: {reference_number or 'N/A'}\n\n"
                f"📥 *Download Official PDF Receipt Voucher:*\n"
                f"{pdf_url}\n\n"
                f"Thank you,\n"
                f"*Decore Construction Management*"
            )
            
            encoded_text = urllib.parse.quote(whatsapp_msg)
            wa_url = f"https://wa.me/{clean_phone}?text={encoded_text}"
            
            messages.success(
                request, 
                f"Weekly payment of ₹{unpaid_balance:,.2f} for {employee.name} recorded successfully.",
                extra_tags=wa_url
            )

        return redirect(f"{reverse('salaries:list')}?period={end_date.strftime('%Y-%m-%d')}")


class SalaryPayAllView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        period = request.POST.get("period", "")
        start_date, end_date = parse_week_period(period)

        paid_count = 0
        total_paid_amount = Decimal("0.00")

        with transaction.atomic():
            # Get all preview rows for the week
            salaries = payroll_preview(start_date, end_date)
            for row in salaries:
                if row.unpaid_balance > 0:
                    # Retrieve or create SalaryRecord
                    salary, created = SalaryRecord.objects.get_or_create(
                        employee=row.employee,
                        week_end_date=end_date,
                        defaults={
                            'daily_wage': row.daily_wage,
                            'present_days': row.present_days,
                            'bonus': row.bonus,
                            'deductions': row.deductions,
                            'net_salary': row.net_salary,
                            'status': SalaryStatus.PENDING
                        }
                    )
                    
                    if not created:
                        salary.daily_wage = row.daily_wage
                        salary.present_days = row.present_days
                        salary.bonus = row.bonus
                        salary.deductions = row.deductions
                        salary.recalculate()
                    
                    # Log the full pending balance payment
                    unpaid = salary.net_salary - sum(p.amount for p in salary.payments.all())
                    if unpaid > 0:
                        Payment.objects.create(
                            salary=salary,
                            employee=row.employee,
                            amount=unpaid,
                            method=Payment.Method.CASH,  # default to cash for bulk pay
                            reference_number="BULK-PAY",
                        )
                        salary.status = SalaryStatus.COMPLETED
                        salary.paid_at = timezone.now()
                        salary.save()

                        paid_count += 1
                        total_paid_amount += unpaid

        if paid_count > 0:
            messages.success(request, f"Successfully recorded bulk weekly payments of ₹{total_paid_amount:,.2f} for {paid_count} workers.")
        else:
            messages.info(request, "No pending salary balances found for this period.")

        return redirect(f"{reverse('salaries:list')}?period={end_date.strftime('%Y-%m-%d')}")


class SalaryReceiptPdfView(View):
    def get(self, request, pk, *args, **kwargs):
        # Allow access if user is logged in, OR if a valid secure receipt token is provided
        if not request.user.is_authenticated:
            token = request.GET.get('token')
            expected_token = get_salary_receipt_token(pk)
            if not token or token != expected_token:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Access Denied: Invalid or missing secure receipt token.")

        salary = get_object_or_404(SalaryRecord, pk=pk)
        from reports.pdf_generator import generate_salary_receipt_pdf
        
        data = {
            'employee_id': salary.employee.id,
            'employee_name': salary.employee.name,
            'employee_role': salary.employee.role,
            'phone': salary.employee.phone,
            'worksite_name': salary.employee.worksite.name if salary.employee.worksite else "General Worksites",
            'period_str': f"Week Ending {salary.week_end_date.strftime('%b %d, %Y')}",
            'paid_date': salary.paid_at.strftime("%d %b %Y, %I:%M %p") if salary.paid_at else timezone.now().strftime("%d %b %Y"),
            'daily_wage': float(salary.daily_wage),
            'present_days': float(salary.present_days),
            'bonus': float(salary.bonus),
            'deductions': float(salary.deductions),
            'net_salary': float(salary.net_salary),
            'paid_amount': float(sum(p.amount for p in salary.payments.all())),
            'payment_method': "Bank Transfer / UPI",
            'reference_number': f"REF-{salary.id}"
        }
        
        pdf = generate_salary_receipt_pdf(data)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Salary_Voucher_{salary.employee.name}_{salary.week_end_date}.pdf"'
        return response
