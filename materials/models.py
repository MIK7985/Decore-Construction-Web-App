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


from django.utils import timezone

class MaterialDelivery(models.Model):
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="deliveries")
    supplier = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=MaterialStatus.choices, default=MaterialStatus.PENDING)
    delivery_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-delivery_date", "-created_at"]

    def __str__(self):
        return f"Delivery from {self.supplier} to {self.worksite.name} ({self.delivery_date})"

    @property
    def total_cost(self):
        return sum(item.total_cost for item in self.items.all())


class Material(models.Model):
    delivery = models.ForeignKey(MaterialDelivery, on_delete=models.CASCADE, related_name="items")
    catalog_item = models.ForeignKey(MaterialCatalog, on_delete=models.SET_NULL, null=True, blank=True, related_name="logged_materials")
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity * self.unit_price

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} — {self.quantity} {self.unit}"
