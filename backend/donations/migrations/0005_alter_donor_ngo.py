# Generated by Django 4.2.10 on 2024-02-20 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0004_alter_donor_date_created_alter_ngo_date_created"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donor",
            name="ngo",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="donations.ngo", verbose_name="NGO"
            ),
        ),
    ]
