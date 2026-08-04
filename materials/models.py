from django.db import models
from worksites.models import Worksite


class MaterialStatus(models.TextChoices):
    DELIVERED = "Delivered", "Delivered"
    ORDERED = "Ordered", "Ordered"
    PENDING = "Pending", "Pending"


class MaterialCatalog(models.Model):
    name = models.CharField(max_length=150, unique=True)
    default_unit = models.CharField(max_length=30)
    default_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    default_supplier = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.default_unit}) — ₹{self.default_unit_price}"


class Material(models.Model):
    catalog_item = models.ForeignKey(MaterialCatalog, on_delete=models.SET_NULL, null=True, blank=True, related_name="logged_materials")
    name = models.CharField(max_length=100)
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="materials")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    used_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    unit = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=MaterialStatus.choices, default=MaterialStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity * self.unit_price

    @property
    def balance_quantity(self):
        return self.quantity - self.used_quantity

    @property
    def used_cost(self):
        return self.used_quantity * self.unit_price

    @property
    def balance_cost(self):
        return self.balance_quantity * self.unit_price

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.quantity} {self.unit}"
