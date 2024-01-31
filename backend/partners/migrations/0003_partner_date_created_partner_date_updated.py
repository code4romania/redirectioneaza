# Generated by Django 4.2.9 on 2024-01-31 20:49

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("partners", "0002_partner_has_custom_header_partner_has_custom_note"),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="date_created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now, verbose_name="date created"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="partner",
            name="date_updated",
            field=models.DateTimeField(auto_now=True, verbose_name="date updated"),
        ),
    ]
