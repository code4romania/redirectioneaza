# Generated by Django 5.1.6 on 2025-02-28 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0024_alter_cause_prefilled_form"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donor",
            name="f_name",
            field=models.CharField(blank=True, db_index=True, default="", max_length=100, verbose_name="first name"),
        ),
        migrations.AlterField(
            model_name="donor",
            name="l_name",
            field=models.CharField(blank=True, db_index=True, default="", max_length=100, verbose_name="last name"),
        ),
        migrations.AlterField(
            model_name="donor",
            name="phone",
            field=models.CharField(blank=True, db_index=True, default="", max_length=30, verbose_name="telephone"),
        ),
    ]
