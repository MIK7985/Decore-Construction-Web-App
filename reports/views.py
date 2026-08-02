from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

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
            cost=ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField(max_digits=15, decimal_places=2))
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        expenses_total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # If all totals are zero, fallback to beautiful dummy data to keep chart readable
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
