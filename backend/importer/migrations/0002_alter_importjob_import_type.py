# Generated by Django 4.2.10 on 2024-02-16 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("importer", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importjob",
            name="import_type",
            field=models.CharField(
                choices=[
                    ("users.User", "User"),
                    ("donations.Ngo", "Ngo"),
                    ("donations.Donor", "Donor"),
                    ("partners.Partner", "Partner"),
                ],
                max_length=32,
                verbose_name="Import type",
            ),
        ),
    ]
