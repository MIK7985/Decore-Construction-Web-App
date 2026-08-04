from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from worksites.models import Worksite
from payments.models import Payment

class SubcontractCategory(models.TextChoices):
    ELECTRICAL = "electrical", "Electrical Work"
    PLUMBING = "plumbing", "Plumbing & Sanitary"
    TILING = "tiling", "Tiling & Flooring"
    PAINTING = "painting", "Painting & Polishing"
    INTERIOR = "interior", "Interior & Woodwork"
    ROOFING = "roofing", "Roofing & Steel Structure"
    FALSE_CEILING = "false_ceiling", "Gypsum & False Ceiling"
    MASONRY = "masonry", "Masonry & Concrete"
    OTHER = "other", "Other Subcontract"

class SubcontractStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    ON_HOLD = "on_hold", "On Hold"

class Subcontract(models.Model):
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="subcontracts")
    contractor_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, help_text="Subcontractor contact phone number for WhatsApp receipts")
    trade = models.CharField(max_length=50, choices=SubcontractCategory.choices, default=SubcontractCategory.OTHER)
    title = models.CharField(max_length=200)
    contract_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=SubcontractStatus.choices, default=SubcontractStatus.IN_PROGRESS)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contractor_name} - {self.title} ({self.worksite.name})"

    @property
    def paid_amount(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance_amount(self):
        return max(self.contract_amount - self.paid_amount, Decimal("0.00"))

    @property
    def progress_percent(self):
        if self.contract_amount > 0:
            pct = (float(self.paid_amount) / float(self.contract_amount)) * 100
            return min(round(pct, 1), 100.0)
        return 0.0


class SubcontractPayment(models.Model):
    subcontract = models.ForeignKey(Subcontract, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(max_length=30, choices=Payment.Method.choices, default=Payment.Method.BANK_TRANSFER)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="subcontract_payments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"₹{self.amount} to {self.subcontract.contractor_name} on {self.payment_date}"

    @property
    def secure_token(self):
        import hashlib
        from django.conf import settings
        return hashlib.sha256(f"subcontract-payment-{self.pk}-{settings.SECRET_KEY}".encode()).hexdigest()[:16]

    @property
    def receipt_url(self):
        from django.urls import reverse
        return reverse("subcontracts:payment_pdf", kwargs={"pk": self.pk}) + f"?token={self.secure_token}"
