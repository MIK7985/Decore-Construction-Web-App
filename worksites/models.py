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
        return sum(item.total_cost for delivery in self.deliveries.all() for item in delivery.items.all())

    @property
    def onsite_materials(self):
        from materials.models import Material, MaterialStatus, SiteStockUsage
        raw_items = Material.objects.filter(
            delivery__worksite=self,
            delivery__status=MaterialStatus.DELIVERED
        ).select_related("delivery")

        # Group delivered quantities by (name, unit)
        groups = {}
        for item in raw_items:
            key = (item.name.strip().title(), item.unit.strip().upper())
            if key not in groups:
                groups[key] = {"quantity": 0.0, "total_val": 0.0}
            groups[key]["quantity"] += float(item.quantity)
            groups[key]["total_val"] += float(item.quantity * item.unit_price)

        # Aggregate consumed quantities from SiteStockUsage
        usage_qs = SiteStockUsage.objects.filter(worksite=self)
        usage_map = {}
        for u in usage_qs:
            key = (u.material_name.strip().title(), u.unit.strip().upper())
            usage_map[key] = usage_map.get(key, 0.0) + float(u.used_quantity)

        res = []
        for (name, unit), data in groups.items():
            qty = data["quantity"]
            total_val = data["total_val"]
            avg_p = (total_val / qty) if qty > 0 else 0.0
            used = usage_map.get((name, unit), 0.0)
            balance = max(qty - used, 0.0)
            res.append({
                "name": name,
                "unit": unit,
                "quantity": qty,
                "used_quantity": used,
                "balance_quantity": balance,
                "unit_price": avg_p,
                "total_cost": total_val
            })
        return sorted(res, key=lambda x: x["name"])

    @property
    def labor_cost(self):
        from decimal import Decimal
        records = self.attendance_records.select_related("employee").all()
        total_labor = Decimal("0.00")
        for record in records:
            status_clean = record.status.lower() if record.status else ""
            if status_clean == "present":
                total_labor += record.employee.wage
            elif status_clean == "late":
                total_labor += record.employee.wage * Decimal("0.5")
            elif status_clean == "overtime":
                total_labor += record.employee.wage * Decimal("1.5")
        return total_labor

    @property
    def expense_cost(self):
        return sum(e.amount for e in self.expenses.all())

    @property
    def total_spend(self):
        return self.spend + self.material_cost + self.labor_cost + self.expense_cost

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


class DocumentCategory(models.TextChoices):
    PERMIT = "permit", "Building Permit"
    DRAWING = "drawing", "Approved Drawing"
    PHOTO = "photo", "Site Photo"
    AGREEMENT = "agreement", "Agreement / Contract"
    BOQ = "boq", "BOQ (Bill of Quantities)"
    INVOICE = "invoice", "Material Invoice"
    OTHER = "other", "Other Attachment"


class WorksiteDocument(models.Model):
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=DocumentCategory.choices, default=DocumentCategory.OTHER)
    file = models.FileField(upload_to="worksites/documents/")
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    notes = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_documents")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @property
    def formatted_size(self):
        size = self.file_size or (self.file.size if self.file and hasattr(self.file, 'size') else 0)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    @property
    def file_extension(self):
        if self.file and self.file.name:
            import os
            ext = os.path.splitext(self.file.name)[1].lower()
            return ext.replace('.', '')
        return ''

    @property
    def is_image(self):
        return self.file_extension in ['jpg', 'jpeg', 'png', 'webp', 'gif']


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = "bank_transfer", "Bank Transfer / NEFT"
    UPI = "upi", "UPI / GPay / PhonePe"
    CHEQUE = "cheque", "Cheque"
    CASH = "cash", "Cash"


class ClientPayment(models.Model):
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="client_payments")
    milestone = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=32, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    reference_number = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    receipt_file = models.FileField(upload_to="worksites/client_receipts/", null=True, blank=True)
    notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"{self.worksite.name} — ₹{self.amount} ({self.milestone})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_worksite_client_paid()

    def delete(self, *args, **kwargs):
        worksite = self.worksite
        super().delete(*args, **kwargs)
        total = sum(p.amount for p in worksite.client_payments.all())
        worksite.client_paid = total
        worksite.save()

    def update_worksite_client_paid(self):
        total = sum(p.amount for p in self.worksite.client_payments.all())
        self.worksite.client_paid = total
        self.worksite.save()


class DailySiteLog(models.Model):
    worksite = models.ForeignKey(Worksite, on_delete=models.CASCADE, related_name="daily_logs")
    date = models.DateField()
    title = models.CharField(max_length=200)
    notes = models.TextField()
    photo = models.ImageField(upload_to="worksites/site_logs/", null=True, blank=True)
    progress_percent = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.worksite.name} ({self.date}): {self.title}"
