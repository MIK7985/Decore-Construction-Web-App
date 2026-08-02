from django.db import models
from django.utils import timezone

from employees.models import Employee
from salaries.models import SalaryRecord


class Payment(models.Model):
    class Method(models.TextChoices):
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CASH = "cash", "Cash"
        UPI = "upi", "UPI"

    salary = models.ForeignKey(SalaryRecord, on_delete=models.PROTECT, related_name="payments", null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BANK_TRANSFER)
    reference_number = models.CharField(max_length=100, blank=True)
    paid_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-paid_on"]

    def __str__(self):
        return f"{self.employee} — ₹{self.amount}"
