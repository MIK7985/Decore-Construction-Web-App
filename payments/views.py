from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import ListView

from .models import Payment


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"
    context_object_name = "payments"

    def get_queryset(self):
        return Payment.objects.select_related("employee", "salary")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
        context["stats"] = {"total_payments": total, "cleared": total, "pending": 0}
        return context
