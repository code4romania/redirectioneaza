from django.test import TestCase
from django.urls import reverse

from donations.models.ngos import Cause, CauseVisibilityChoices, Donor, Ngo
from redirectioneaza.common.testing import ApexClient

# A simple 1x1 pixel transparent PNG image encoded in base64 for testing signature input
SIGNATURE_TEST_STRING = """data:image/png;base64,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"""


class RedirectionFormSignatureTests(TestCase):
    def setUp(self):
        self.client = ApexClient()
        self.ngo = Ngo.objects.create(name="Test NGO", registration_number="6859662")
        self.visible_cause = Cause.objects.create(
            ngo=self.ngo,
            name="Test Cause",
            slug="test-public-cause",
            visibility=CauseVisibilityChoices.PUBLIC,
            allow_online_collection=True,
            bank_account="RO25RZBR6782146545912934",
        )
        self.private_cause = Cause.objects.create(
            ngo=self.ngo,
            name="Test Private Cause",
            slug="test-private-cause",
            visibility=CauseVisibilityChoices.PRIVATE,
            allow_online_collection=True,
            bank_account="RO83PORL2765427342671968",
        )

        self.form_input = {
            "agree_contact": "on",
            "agree_terms": "on",
            "anaf_gdpr": "on",
            "apartment": "3",
            "cnp": "1920129417564",
            "county": "Argeș",
            "csrfmiddlewaretoken": "",
            "email_address": "test@example.com",
            "entrance": "f",
            "f_name": "bbb",
            "flat": "e",
            "floor": "2",
            "g-recaptcha-response": "123",
            "initial": "c",
            "l_name": "aaa",
            "locality": "Pitesti",
            "phone_number": "0770123456",
            "signature": SIGNATURE_TEST_STRING,
            "street_name": "ddd",
            "street_number": "1",
            "two_years": "on",
        }

    def test_cannot_access_private_cause(self):
        response = self.client.get(reverse("twopercent", args=["test-private-cause"]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse("twopercent", args=["test-private-cause"]), self.form_input)
        self.assertEqual(response.status_code, 404)

    def test_sign_a_form(self):
        response = self.client.get(reverse("twopercent", args=["test-public-cause"]))
        self.assertEqual(response.status_code, 200)

        existing_count = Donor.objects.filter(cause=self.visible_cause).count()
        self.assertEqual(existing_count, 0)

        response = self.client.post(reverse("twopercent", args=["test-public-cause"]), self.form_input)
        self.assertRedirects(response, reverse("ngo-twopercent-success", args=["test-public-cause"]))

        existing_count = Donor.objects.filter(cause=self.visible_cause).count()
        self.assertEqual(existing_count, 1)
