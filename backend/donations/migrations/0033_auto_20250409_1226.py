# Generated by Django 5.1.7 on 2025-04-09 09:26

from django.db import migrations
from django.db.models.aggregates import Count


def set_first_cause_to_main(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Ngo = apps.get_model("donations", "Ngo")

    ngos_with_one_cause = Ngo.objects.annotate(num_causes=Count("causes")).filter(num_causes=1)
    Cause.objects.filter(ngo__in=ngos_with_one_cause).exclude(is_main=True).update(is_main=True)


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0032_initialize_notifications_email"),
    ]

    operations = [
        migrations.RunPython(set_first_cause_to_main, reverse_code=migrations.RunPython.noop),
    ]
