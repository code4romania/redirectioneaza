# Generated by Django 4.2.10 on 2024-02-22 12:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("donations", "0007_alter_donor_date_created_alter_ngo_date_created"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="job",
            options={
                "get_latest_by": "date_created",
                "ordering": ["-date_created"],
                "verbose_name": "job",
                "verbose_name_plural": "jobs",
            },
        ),
        migrations.AlterField(
            model_name="job",
            name="ngo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="donations.ngo", verbose_name="NGO"
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to=settings.AUTH_USER_MODEL,
                verbose_name="owner",
            ),
        ),
    ]