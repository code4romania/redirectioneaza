# Generated by Django 4.2.9 on 2024-02-01 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0006_alter_donor_pdf_file_alter_ngo_prefilled_form"),
    ]

    operations = [
        migrations.AddField(
            model_name="donor",
            name="address",
            field=models.JSONField(blank=True, default=dict, verbose_name="address"),
        ),
    ]
