import django.db.models.deletion
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = [("employees", "0004_employee_is_archived")]
    operations = [migrations.CreateModel(name="SalaryRecord", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("year", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(2000)])),
        ("month", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
        ("daily_wage", models.DecimalField(decimal_places=2, max_digits=10)),
        ("present_days", models.DecimalField(decimal_places=1, default=0, max_digits=5)),
        ("bonus", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        ("deductions", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        ("net_salary", models.DecimalField(decimal_places=2, max_digits=12)),
        ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid")], default="pending", max_length=10)),
        ("generated_at", models.DateTimeField(auto_now_add=True)),
        ("paid_at", models.DateTimeField(blank=True, null=True)),
        ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="salary_records", to="employees.employee")),
    ], options={"ordering": ["-year", "-month", "employee__name"]}), migrations.AddConstraint(model_name="salaryrecord", constraint=models.UniqueConstraint(fields=("employee", "year", "month"), name="unique_employee_salary_period"))]
