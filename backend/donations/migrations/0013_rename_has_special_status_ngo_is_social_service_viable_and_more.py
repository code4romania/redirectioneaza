# Generated by Django 5.1.1 on 2024-09-27 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0012_remove_ngo_form_url_remove_ngo_image_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="ngo",
            old_name="has_special_status",
            new_name="is_social_service_viable",
        ),
        migrations.AddField(
            model_name="ngo",
            name="filename_cache",
            field=models.JSONField(default=dict, editable=False, verbose_name="Filename cache"),
        ),
        migrations.AddField(
            model_name="ngo",
            name="ngohub_last_update_ended",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Last NGO Hub update"),
        ),
        migrations.AddField(
            model_name="ngo",
            name="ngohub_last_update_started",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="Last NGO Hub update"),
        ),
        migrations.AddField(
            model_name="ngo",
            name="ngohub_org_id",
            field=models.IntegerField(
                blank=True, db_index=True, null=True, unique=True, verbose_name="NGO Hub organization ID"
            ),
        ),
    ]
