from django.db import models
from django.utils import timezone
from worksites.models import Worksite

class ExpenseCategory(models.TextChoices):
    FUEL = "Fuel", "Fuel"
    MACHINERY_RENTAL = "Machinery Rental", "Machinery Rental"
    UTILITIES = "Utilities", "Utilities"
    SAFETY_GEAR = "Safety Gear", "Safety Gear"
    PERMITS = "Permits", "Permits"

class ExpenseStatus(models.TextChoices):
    APPROVED = "Approved", "Approved"
    PENDING = "Pending", "Pending"

class Expense(models.Model):
    category = models.CharField(max_length=50, choices=ExpenseCategory.choices, default=ExpenseCategory.FUEL)
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ExpenseStatus.choices, default=ExpenseStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.worksite.name})"
