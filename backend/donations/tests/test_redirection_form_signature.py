from django.test import TestCase
from django.urls import reverse

from donations.models.ngos import Cause, CauseVisibilityChoices, Donor, Ngo
from redirectioneaza.common.testing import ApexClient


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
            "signature": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB2aWV3Qm94PSIwIDAgNDYzLjgzMzMzMzMzMzMzMzM3IDE1NC45MTY2NjY2NjY2NjY2OSIgd2lkdGg9IjQ2My44MzMzMzMzMzMzMzMzNyIgaGVpZ2h0PSIxNTQuOTE2NjY2NjY2NjY2NjkiPjxjaXJjbGUgcj0iMS41IiBjeD0iMTg4LjkxNjY4NzAxMTcxODc1IiBjeT0iODQuMjQ5OTg0NzQxMjEwOTQiIGZpbGw9ImJsYWNrIj48L2NpcmNsZT48Y2lyY2xlIHI9IjEuNSIgY3g9IjIwMy41ODMzMTI5ODgyODEyNSIgY3k9IjYyLjI0OTk4NDc0MTIxMDk0IiBmaWxsPSJibGFjayI+PC9jaXJjbGU+PGNpcmNsZSByPSIxLjUiIGN4PSIyMTguMjUiIGN5PSI4NC4yNDk5ODQ3NDEyMTA5NCIgZmlsbD0iYmxhY2siPjwvY2lyY2xlPjwvc3ZnPg==",
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
