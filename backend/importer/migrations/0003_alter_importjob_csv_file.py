# Generated by Django 4.2.10 on 2024-02-21 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("importer", "0002_alter_importjob_import_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importjob",
            name="csv_file",
            field=models.FileField(upload_to="imports/%Y/%m/%d/", verbose_name="File"),
        ),
    ]
