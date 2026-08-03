from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from employees.models import Employee


class SalaryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"


class SalaryRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="salary_records")
    year = models.PositiveIntegerField(validators=[MinValueValidator(2000)], null=True, blank=True)
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], null=True, blank=True)
    week_end_date = models.DateField(null=True, blank=True)
    daily_wage = models.DecimalField(max_digits=10, decimal_places=2)
    present_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=SalaryStatus.choices, default=SalaryStatus.PENDING)
    generated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-week_end_date", "-year", "-month", "employee__name"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "week_end_date"], name="unique_employee_weekly_salary_period")
        ]
        indexes = [
            models.Index(fields=["week_end_date"], name="salary_week_end_idx"),
            models.Index(fields=["week_end_date", "status"], name="salary_week_status_idx"),
        ]

    def recalculate(self):
        self.net_salary = (self.daily_wage * self.present_days) + self.bonus - self.deductions

    def save(self, *args, **kwargs):
        self.recalculate()
        if self.week_end_date:
            self.year = self.week_end_date.year
            self.month = self.week_end_date.month
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — Week {self.week_end_date}"
