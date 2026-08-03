from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View

from worksites.models import Worksite
from .models import Expense, ExpenseStatus


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        return Expense.objects.select_related("worksite").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        
        # Calculate stats dynamically
        total_val = qs.aggregate(total=Sum('amount'))['total'] or 0.00
        approved_val = qs.filter(status=ExpenseStatus.APPROVED).aggregate(total=Sum('amount'))['total'] or 0.00
        pending_val = qs.filter(status=ExpenseStatus.PENDING).aggregate(total=Sum('amount'))['total'] or 0.00
        
        context["stats"] = {
            "total_expenses": float(total_val),
            "approved": float(approved_val),
            "pending": float(pending_val)
        }
        context["worksites"] = Worksite.objects.order_by("name")
        return context


class ExpenseCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        category = request.POST.get("category")
        worksite_id = request.POST.get("worksite")
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        description = request.POST.get("description")
        status = request.POST.get("status", ExpenseStatus.PENDING)
        receipt = request.FILES.get("receipt")

        if not all([category, worksite_id, amount, date, description]):
            return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

        try:
            worksite = get_object_or_404(Worksite, id=worksite_id)
            expense = Expense.objects.create(
                category=category,
                worksite=worksite,
                amount=amount,
                date=date,
                description=description,
                status=status,
                receipt=receipt
            )
            return JsonResponse({
                "success": True, 
                "message": f"Expense of ₹{expense.amount} for '{expense.category}' saved successfully."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class ExpenseApproveView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            expense = get_object_or_404(Expense, pk=pk)
            expense.status = ExpenseStatus.APPROVED
            expense.save()
            return JsonResponse({
                "success": True, 
                "message": f"Expense of ₹{expense.amount} approved successfully."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
