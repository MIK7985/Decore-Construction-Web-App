from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from employees.models import Employee
from worksites.models import Worksite, WorksiteStatus

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.db.models import Sum
        active_sites = Worksite.objects.filter(status=WorksiteStatus.ACTIVE)
        aggregates = active_sites.aggregate(total_budget=Sum('budget'), total_spend=Sum('spend'))
        total_value = aggregates['total_budget'] or 0
        total_spend = aggregates['total_spend'] or 0
        
        context["stats"] = {
            "total_employees": Employee.objects.filter(is_archived=False).count(),
            "active_worksites": active_sites.count(),
            "payments_month": float(total_spend),
            "pending_expenses": float(total_value - total_spend) if total_value > total_spend else 0.0,
        }
        context["activities"] = []
        return context
