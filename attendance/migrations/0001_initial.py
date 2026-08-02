import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("employees", "0004_employee_is_archived"), ("worksites", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("check_in", models.TimeField(blank=True, null=True)),
                ("check_out", models.TimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("present", "Present"), ("late", "Late"), ("absent", "Absent"), ("on_leave", "On Leave")], default="present", max_length=16)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="employees.employee")),
                ("worksite", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_records", to="worksites.worksite")),
            ],
            options={"ordering": ["-date", "employee__name"]},
        ),
        migrations.AddConstraint(model_name="attendance", constraint=models.UniqueConstraint(fields=("employee", "date"), name="unique_employee_attendance_date")),
    ]
