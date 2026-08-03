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
    status = models.CharField(max_length=16, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__name"]
        constraints = [models.UniqueConstraint(fields=["employee", "date"], name="unique_employee_attendance_date")]

    def __str__(self):
        return f"{self.employee} — {self.date}"
