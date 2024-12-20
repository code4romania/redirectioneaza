# Generated by Django 5.1.4 on 2024-12-20 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0016_remove_donor_pdf_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ngo",
            name="is_accepting_forms",
            field=models.BooleanField(db_index=True, default=True, verbose_name="is accepting forms"),
        ),
    ]
