# Generated by Django 5.1.6 on 2025-02-14 10:47

from django.db import migrations


def move_forms_data(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Ngo = apps.get_model("donations", "Ngo")

    for ngo in Ngo.objects.all():
        ngo_form = Cause(
            ngo=ngo,
            allow_online_collection=ngo.is_accepting_forms,
            display_image=ngo.logo,
            slug=ngo.slug,
            name=ngo.name,
            description=ngo.description,
            bank_account=ngo.bank_account,
        )

        ngo_form.save()


def move_forms_data_reverse(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Ngo = apps.get_model("donations", "Ngo")

    for ngo in Ngo.objects.filter(causes__isnull=False):
        # get the oldest form of the NGO
        ngo_form: Cause = ngo.causes.order_by("date_created").first()

        ngo.logo = ngo_form.display_image
        ngo.slug = ngo_form.slug
        ngo.description = ngo_form.description
        ngo.bank_account = ngo_form.bank_account
        ngo.save()

        ngo.causes.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("donations", "0022_cause"),
    ]

    operations = [
        migrations.RunPython(move_forms_data, reverse_code=move_forms_data_reverse),
    ]
