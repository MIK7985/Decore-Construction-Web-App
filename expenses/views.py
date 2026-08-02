from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ExpenseListView(LoginRequiredMixin, TemplateView):
    template_name = "expenses/expense_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = []
        context["stats"] = {"total_expenses": 0, "approved": 0, "pending": 0}
        return context
