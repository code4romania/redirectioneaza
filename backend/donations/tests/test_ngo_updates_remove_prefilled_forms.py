import copy
import random

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from donations.models import Cause, Ngo
from donations.models.ngos import CauseVisibilityChoices
from redirectioneaza.common.testing import ApexClient


class NgoPrefilledFormsUpdate(TestCase):
    def setUp(self):
        self.client = ApexClient()
        self.ngo = Ngo.objects.create(
            name="Test NGO",
            registration_number="6859662",
            email="testngo@example.com",
            address="Test Address",
            county="Arad",
            active_region="Arad",
            has_online_tax_account=True,
        )
        self.user = get_user_model().objects.create_user(
            username="test_user",
            password="test_password",
            email="testuser@example.com",
            ngo=self.ngo,
        )
        self.client.force_login(self.user)

        self.cause_1 = Cause.objects.create(
            ngo=self.ngo,
            name="Test First Cause",
            description="Test First Cause description",
            is_main=True,
            slug="test-first-cause",
            visibility=CauseVisibilityChoices.PUBLIC,
            allow_online_collection=True,
            bank_account="RO70PORL6641918584933675",
        )
        self.cause_2 = Cause.objects.create(
            ngo=self.ngo,
            name="Test Second Cause",
            description="Test Second Cause description",
            is_main=False,
            slug="test-second-cause",
            visibility=CauseVisibilityChoices.PUBLIC,
            allow_online_collection=True,
            bank_account="RO33PORL9731244852871472",
        )

        self.other_ibans = [
            "RO24RZBR3547369388477816",
            "RO67RZBR7144423889878185",
            "RO68RZBR6969652621537361",
            "RO70RZBR6376267914758588",
            "RO31PORL7564484283991911",
            "RO02RZBR5847685559188868",
            "RO07RZBR9326845858982858",
            "RO05PORL3799716933582794",
            "RO52RZBR3933822677666831",
            "RO04PORL5687618387868878",
        ]

        self.other_cifs = [
            "5212840396",
            "5726275222",
            "8441714601",
            "5654429712",
            "4659866692",
            "19",
        ]

        self.default_update_payload = {
            "cif": self.ngo.registration_number,
            "name": self.ngo.name,
            "email": self.ngo.email,
            "address": self.ngo.address,
            "county": self.ngo.county,
            "contact_email": self.ngo.email,
            "active_region": self.ngo.active_region,
            "has_spv_option": "yes",
        }

    def test_can_access_prefilled_form(self):
        prefilled_form_url = reverse("api-cause-form", kwargs={"cause_slug": self.cause_1.slug})

        # Check that the initial prefilled_form is empty
        self.assertEqual(self.cause_1.prefilled_form.name, "")

        # Access the prefilled_form URL to generate the initial prefilled_form
        response = self.client.get(prefilled_form_url)
        self.assertEqual(response.status_code, 302)

        # Check that the prefilled_form has been created
        cause_1_with_prefilled_form = Cause.objects.get(pk=self.cause_1.pk)
        self.assertEqual(response.url, cause_1_with_prefilled_form.prefilled_form.url)

    @override_settings(DEFAULT_RUN_METHOD="sync")
    def test_cause_iban_change_updates_prefilled_form(self):
        prefilled_form_url = reverse("api-cause-form", kwargs={"cause_slug": self.cause_1.slug})

        # Check that the initial prefilled_form is empty
        self.assertEqual(self.cause_1.prefilled_form.name, "")

        # Access the prefilled_form URL to generate the initial prefilled_form
        self.client.get(prefilled_form_url)

        self.cause_1.refresh_from_db()

        # Change the bank account of the cause
        new_iban: str = random.choice(self.other_ibans)
        self.assertNotEqual(new_iban, self.cause_1.bank_account)

        # Set up a payload to update the cause IBAN
        payload = {
            "bank_account": new_iban,
            "name": self.cause_1.name,
            "description": self.cause_1.description,
            "slug": self.cause_1.slug,
            "visibility": self.cause_1.visibility,
            "is_main": self.cause_1.is_main,
            "allow_online_notifications": self.cause_1.allow_online_notifications,
        }
        response = self.client.post(reverse("my-organization:form"), payload)
        self.assertEqual(response.status_code, 200)

        # Check that the prefilled_form has been removed
        self.cause_1.refresh_from_db()
        self.assertEqual(self.cause_1.prefilled_form.name, "")

        self.assertEqual(new_iban, self.cause_1.bank_account)

    @override_settings(DEFAULT_RUN_METHOD="sync")
    def test_ngo_changes_update_prefilled_forms(self):
        prefilled_form_cause_1 = reverse("api-cause-form", kwargs={"cause_slug": self.cause_1.slug})
        prefilled_form_cause_2 = reverse("api-cause-form", kwargs={"cause_slug": self.cause_2.slug})

        # Check that the initial prefilled_forms are empty
        self.assertEqual(self.cause_1.prefilled_form.name, "")
        self.assertEqual(self.cause_2.prefilled_form.name, "")

        # Access the prefilled_form URL to generate the initial prefilled_form
        self.client.get(prefilled_form_cause_1)
        self.client.get(prefilled_form_cause_2)

        # Check that the initial prefilled_forms exist
        self.cause_1.refresh_from_db()
        self.cause_2.refresh_from_db()

        self.assertNotEqual(self.cause_1.prefilled_form.name, "")
        self.assertNotEqual(self.cause_2.prefilled_form.name, "")

        # Change the registration_number of the NGO
        new_registration_number = random.choice(self.other_cifs)
        if new_registration_number.startswith("RO"):
            # Remove the "RO" prefix if it exists
            new_registration_number = new_registration_number[2:]
        self.assertNotEqual(new_registration_number, self.ngo.registration_number)

        ngo_update_url = reverse("my-organization:presentation")
        update_cif_payload = copy.deepcopy(self.default_update_payload)
        update_cif_payload["cif"] = new_registration_number
        self.client.post(ngo_update_url, update_cif_payload)

        # Check that the NGO registration_number has been updated
        self.ngo.refresh_from_db()
        self.assertEqual(self.ngo.registration_number, new_registration_number)

        # Check that the prefilled_forms have been removed
        self.cause_1.refresh_from_db()
        self.cause_2.refresh_from_db()

        self.assertEqual(self.cause_1.prefilled_form.name, "")
        self.assertEqual(self.cause_2.prefilled_form.name, "")

        # Access the prefilled_form URL to generate the initial prefilled_form
        self.client.get(prefilled_form_cause_1)
        self.client.get(prefilled_form_cause_2)

        # Check that the initial prefilled_forms exist
        self.cause_1.refresh_from_db()
        self.cause_2.refresh_from_db()

        self.assertNotEqual(self.cause_1.prefilled_form.name, "")
        self.assertNotEqual(self.cause_2.prefilled_form.name, "")

        new_ngo_name = "New name for the NGO"
        self.assertNotEqual(new_ngo_name, self.ngo.name)

        update_name_payload = copy.deepcopy(update_cif_payload)
        update_name_payload["name"] = new_ngo_name
        self.client.post(ngo_update_url, update_name_payload)

        # Check that the NGO name has been updated
        self.ngo.refresh_from_db()
        self.assertEqual(self.ngo.name, new_ngo_name)

        # Check that the prefilled_forms have been removed
        self.cause_1.refresh_from_db()
        self.cause_2.refresh_from_db()

        self.assertEqual(self.cause_1.prefilled_form.name, "")
        self.assertEqual(self.cause_2.prefilled_form.name, "")
