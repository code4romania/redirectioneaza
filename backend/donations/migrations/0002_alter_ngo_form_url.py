# Generated by Django 4.2.8 on 2024-01-03 16:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ngo",
            name="form_url",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="form url"),
        ),
    ]
