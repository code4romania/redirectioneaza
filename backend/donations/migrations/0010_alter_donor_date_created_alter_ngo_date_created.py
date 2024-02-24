# Generated by Django 4.2.10 on 2024-02-23 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0009_alter_donor_date_created_alter_ngo_date_created"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donor",
            name="date_created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="date created"),
        ),
        migrations.AlterField(
            model_name="ngo",
            name="date_created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="date created"),
        ),
    ]