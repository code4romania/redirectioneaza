# Generated by Django 5.1.4 on 2025-01-14 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0019_add_romanian_unaccent"),
    ]

    operations = [
        migrations.AddField(
            model_name="ngo",
            name="display_email",
            field=models.BooleanField(db_index=True, default=False, verbose_name="display email"),
        ),
        migrations.AddField(
            model_name="ngo",
            name="display_phone",
            field=models.BooleanField(db_index=True, default=False, verbose_name="display phone"),
        ),
    ]
