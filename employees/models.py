from django.db import models
from worksites.models import Worksite

class EmployeeStatus(models.TextChoices):
    ACTIVE = "Active", "Active"
    ON_LEAVE = "On Leave", "On Leave"
    INACTIVE = "Inactive", "Inactive"

class Employee(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    worksite = models.ForeignKey(Worksite, on_delete=models.SET_NULL, blank=True, null=True, related_name="employees")
    phone = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE
    )
    wage = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField(blank=True, null=True)
    joined = models.DateField(auto_now_add=True)
    photo = models.FileField(upload_to="employee_photos/", blank=True, null=True)
    id_photo = models.FileField(upload_to="employee_ids/", blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name
