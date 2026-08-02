from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from employees.models import Employee
from worksites.models import Worksite, WorksiteStatus

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate dashboard metrics dynamically from the database
        active_sites = Worksite.objects.filter(status=WorksiteStatus.ACTIVE)
        total_value = sum(s.budget for s in active_sites)
        total_spend = sum(s.spend for s in active_sites)
        
        context["stats"] = {
            "total_employees": Employee.objects.count(),
            "active_worksites": active_sites.count(),
            "payments_month": float(total_spend),
            "pending_expenses": float(total_value - total_spend) if total_value > total_spend else 0.0,
        }
        context["activities"] = []
        return context
