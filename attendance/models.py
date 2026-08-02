from django.core.exceptions import ValidationError
from django.db import models

from employees.models import Employee
from worksites.models import Worksite


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    LATE = "late", "Late"
    ABSENT = "absent", "Absent"
    OVERTIME = "overtime", "Overtime"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    worksite = models.ForeignKey(Worksite, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_records")
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__name"]
        constraints = [models.UniqueConstraint(fields=["employee", "date"], name="unique_employee_attendance_date")]

    def clean(self):
        if self.check_out and self.check_in and self.check_out < self.check_in:
            raise ValidationError("Check-out time cannot be earlier than check-in time.")

    def __str__(self):
        return f"{self.employee} — {self.date}"
