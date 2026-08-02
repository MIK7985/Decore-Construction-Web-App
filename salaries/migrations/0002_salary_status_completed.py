from django.db import migrations, models


def mark_paid_completed(apps, schema_editor):
    SalaryRecord = apps.get_model("salaries", "SalaryRecord")
    SalaryRecord.objects.filter(status="paid").update(status="completed")


class Migration(migrations.Migration):
    dependencies = [("salaries", "0001_initial")]
    operations = [
        migrations.RunPython(mark_paid_completed, migrations.RunPython.noop),
        migrations.AlterField(model_name="salaryrecord", name="status", field=models.CharField(choices=[("pending", "Pending"), ("completed", "Completed")], default="pending", max_length=10)),
    ]
