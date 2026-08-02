from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("employees", "0002_migrate_worksite_relationship")]

    operations = [
        migrations.RemoveField(model_name="employee", name="worksite"),
        migrations.RenameField(model_name="employee", old_name="assigned_worksite", new_name="worksite"),
    ]
