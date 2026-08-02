import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Worksite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True)),
                ("client", models.CharField(max_length=150)),
                ("location", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("active", "Active"), ("on_hold", "On Hold"), ("completed", "Completed")], default="active", max_length=20)),
                ("progress", models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("budget", models.DecimalField(decimal_places=2, max_digits=14)),
                ("start_date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("supervisor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="supervised_worksites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-start_date", "name"]},
        ),
    ]
