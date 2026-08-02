from django.db import migrations, models
import django.db.models.deletion


def copy_worksite_relationships(apps, schema_editor):
    Employee = apps.get_model("employees", "Employee")
    Worksite = apps.get_model("worksites", "Worksite")
    for employee in Employee.objects.exclude(worksite__isnull=True).exclude(worksite=""):
        worksite, _ = Worksite.objects.get_or_create(
            name=employee.worksite,
            defaults={
                "client": "Legacy client",
                "location": "To be updated",
                "budget": 0,
                "start_date": "2026-01-01",
            },
        )
        employee.assigned_worksite = worksite
        employee.save(update_fields=["assigned_worksite"])


class Migration(migrations.Migration):
    dependencies = [("worksites", "0001_initial"), ("employees", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="assigned_worksite",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="employees", to="worksites.worksite"),
        ),
        migrations.RunPython(copy_worksite_relationships, migrations.RunPython.noop),
    ]
