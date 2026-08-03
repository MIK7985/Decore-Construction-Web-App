from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class WorksiteStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"

class Worksite(models.Model):
    name = models.CharField(max_length=150, unique=True)
    client = models.CharField(max_length=150)
    location = models.CharField(max_length=255)
    supervisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="supervised_worksites",
    )
    status = models.CharField(max_length=20, choices=WorksiteStatus.choices, default=WorksiteStatus.ACTIVE)
    progress = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    budget = models.DecimalField(max_digits=14, decimal_places=2)
    spend = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    client_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "name"]

    def __str__(self):
        return self.name

    @property
    def material_cost(self):
        return sum(m.total_cost for m in self.materials.all())

    @property
    def labor_cost(self):
        from attendance.models import AttendanceStatus
        from decimal import Decimal
        records = self.attendance_records.select_related("employee").all()
        total_labor = Decimal("0.00")
        for record in records:
            if record.status == AttendanceStatus.PRESENT or record.status == "present":
                total_labor += record.employee.wage
            elif record.status == AttendanceStatus.LATE or record.status == "late":
                total_labor += record.employee.wage * Decimal("0.5")
            elif record.status == AttendanceStatus.OVERTIME or record.status == "overtime":
                total_labor += record.employee.wage * Decimal("1.5")
        return total_labor

    @property
    def total_spend(self):
        return self.material_cost + self.labor_cost

    @property
    def profit(self):
        return self.budget - self.total_spend

    @property
    def profit_margin(self):
        if self.budget > 0:
            return (self.profit / self.budget) * 100
        return 0

    @property
    def profit_abs(self):
        return abs(self.profit)

    @property
    def client_balance(self):
        return self.budget - self.client_paid


