import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [("employees", "0004_employee_is_archived"), ("salaries", "0002_salary_status_completed")]
    operations = [migrations.CreateModel(name="Payment", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
        ("method", models.CharField(choices=[("bank_transfer", "Bank Transfer"), ("cash", "Cash"), ("upi", "UPI")], default="bank_transfer", max_length=20)),
        ("reference_number", models.CharField(blank=True, max_length=100)),
        ("paid_on", models.DateTimeField(default=django.utils.timezone.now)),
        ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="employees.employee")),
        ("salary", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="payment", to="salaries.salaryrecord")),
    ], options={"ordering": ["-paid_on"]})]
