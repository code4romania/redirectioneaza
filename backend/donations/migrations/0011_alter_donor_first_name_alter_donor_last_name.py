# Generated by Django 4.2.13 on 2024-05-16 07:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0010_alter_donor_date_created_alter_ngo_date_created"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donor",
            name="first_name",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="last name"),
        ),
        migrations.AlterField(
            model_name="donor",
            name="last_name",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="first name"),
        ),
    ]
