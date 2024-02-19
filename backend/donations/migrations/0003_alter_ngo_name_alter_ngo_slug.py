# Generated by Django 4.2.10 on 2024-02-19 08:54

from django.db import migrations, models
import donations.models.main


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ngo",
            name="name",
            field=models.CharField(db_index=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="ngo",
            name="slug",
            field=models.SlugField(
                max_length=150, unique=True, validators=[donations.models.main.ngo_slug_validator], verbose_name="slug"
            ),
        ),
    ]
