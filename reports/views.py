from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "reports/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Summary data for charts
        context['report_stats'] = {
            'employees_count': 0,
            'worksites_count': 0,
            'salaries_total': 0,
            'payments_total': 0,
            'materials_total': 0,
            'expenses_total': 0,
        }
        return context
