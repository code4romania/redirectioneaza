# Generated by Django 5.1.2 on 2024-10-31 14:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0015_rename_last_name_donor_f_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="donor",
            name="pdf_url",
        ),
    ]
