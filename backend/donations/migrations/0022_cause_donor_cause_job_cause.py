# Generated by Django 5.1.6 on 2025-02-18 11:05

import functools

import django.db.models.deletion
from django.db import migrations, models

import donations.models.ngos


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0021_ngo_locality"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cause",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("allow_online_collection", models.BooleanField(default=False, verbose_name="allow online collection")),
                (
                    "display_image",
                    models.ImageField(
                        blank=True,
                        storage=donations.models.ngos.select_public_storage,
                        upload_to=functools.partial(donations.models.ngos.cause_directory_path, *("logos",), **{}),
                        verbose_name="logo",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=150,
                        unique=True,
                        validators=[donations.models.ngos.ngo_slug_validator],
                        verbose_name="slug",
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=200, verbose_name="name")),
                ("description", models.TextField(verbose_name="description")),
                ("bank_account", models.CharField(max_length=100, verbose_name="bank account")),
                (
                    "prefilled_form",
                    models.FileField(
                        blank=True,
                        storage=donations.models.ngos.select_public_storage,
                        upload_to=functools.partial(
                            donations.models.ngos.year_cause_directory_path, *("causes",), **{}
                        ),
                        verbose_name="form with prefilled cause",
                    ),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="date created")),
                ("date_updated", models.DateTimeField(auto_now=True, db_index=True, verbose_name="date updated")),
                (
                    "ngo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="causes", to="donations.ngo"
                    ),
                ),
            ],
            options={
                "verbose_name": "Cause",
                "verbose_name_plural": "Causes",
            },
        ),
        migrations.AddField(
            model_name="donor",
            name="cause",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="donations.cause", verbose_name="cause"
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="cause",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to="donations.cause",
                verbose_name="cause",
            ),
        ),
    ]
