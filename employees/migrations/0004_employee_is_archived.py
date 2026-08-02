from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("employees", "0003_rename_assigned_worksite")]

    operations = [migrations.AddField(model_name="employee", name="is_archived", field=models.BooleanField(default=False))]
