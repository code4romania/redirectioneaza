# Generated by Django 5.1.1 on 2024-09-27 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0011_alter_donor_first_name_alter_donor_last_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ngo",
            name="form_url",
        ),
        migrations.RemoveField(
            model_name="ngo",
            name="image",
        ),
        migrations.RemoveField(
            model_name="ngo",
            name="image_url",
        ),
        migrations.RemoveField(
            model_name="ngo",
            name="logo_url",
        ),
        migrations.RemoveField(
            model_name="ngo",
            name="other_emails",
        ),
        migrations.AddField(
            model_name="ngo",
            name="registration_number_valid",
            field=models.BooleanField(db_index=True, null=True, verbose_name="registration validation failed"),
        ),
        migrations.AddField(
            model_name="ngo",
            name="vat_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=2, verbose_name="VAT ID"),
        ),
    ]