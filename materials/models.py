from django.db import models
from worksites.models import Worksite

class MaterialStatus(models.TextChoices):
    DELIVERED = "Delivered", "Delivered"
    ORDERED = "Ordered", "Ordered"
    PENDING = "Pending", "Pending"

class Material(models.Model):
    name = models.CharField(max_length=100)
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="materials")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=MaterialStatus.choices, default=MaterialStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity * self.unit_price

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.quantity} {self.unit}"
