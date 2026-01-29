from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from donations.models.donors import Donor
from donations.models.ngos import Cause, CauseVisibilityChoices, Ngo
from redirectioneaza.common.testing.client import ApexClient


class RedirectionDisableLinkViewTests(TestCase):
    def setUp(self):
        self.client = ApexClient()
        self.ngo = Ngo.objects.create(
            name="Test NGO",
            registration_number="6859662",
            email="ngo@example.com",
            has_online_tax_account=True,
        )
        self.cause = Cause.objects.create(
            ngo=self.ngo,
            name="Test Cause",
            description="Test Cause description",
            slug="test-cause",
            visibility=CauseVisibilityChoices.PUBLIC,
            allow_online_collection=True,
            bank_account="RO25RZBR6782146545912934",
            is_main=True,
        )
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-password",
            ngo=self.ngo,
        )
        self.donor = Donor.objects.create(
            ngo=self.ngo,
            cause=self.cause,
            email="donor@example.com",
            has_signed=True,
        )

    def test_get_returns_method_not_allowed(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("my-organization:redirection-disable", args=[self.donor.pk]))

        self.assertEqual(response.status_code, 405)

    def test_post_requires_ngo(self):
        user_without_ngo = get_user_model().objects.create_user(
            email="no-ngo@example.com",
            password="test-password",
        )
        self.client.force_login(user_without_ngo)

        response = self.client.post(
            reverse("my-organization:redirection-disable", args=[self.donor.pk]),
            {"disable_redirection": "true"},
        )

        self.assertEqual(response.status_code, 404)

    def test_post_requires_active_ngo(self):
        self.ngo.is_active = False
        self.ngo.save(update_fields=["is_active"])
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("my-organization:redirection-disable", args=[self.donor.pk]),
            {"disable_redirection": "true"},
        )

        self.assertEqual(response.status_code, 403)

    def test_post_requires_confirm_flag(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("my-organization:redirection-disable", args=[self.donor.pk]))

        self.assertEqual(response.status_code, 404)

    def test_post_requires_signed_donor(self):
        donor = Donor.objects.create(
            ngo=self.ngo,
            cause=self.cause,
            email="unsigned@example.com",
            has_signed=False,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("my-organization:redirection-disable", args=[donor.pk]),
            {"disable_redirection": "true"},
        )

        self.assertEqual(response.status_code, 404)

    @patch("donations.views.ngo_account.redirections.extend_email_context", return_value={"site_title": "site"})
    @patch("donations.views.ngo_account.redirections.build_uri", return_value="https://example.com/action")
    @patch("donations.views.ngo_account.redirections.send_email")
    def test_post_disables_redirection_and_notifies_with_cause(
        self,
        send_email,
        build_uri,
        extend_email_context,
    ):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("my-organization:redirection-disable", args=[self.donor.pk]),
            {"disable_redirection": "true"},
        )

        self.assertRedirects(response, reverse("my-organization:redirections"))
        self.donor.refresh_from_db()
        self.assertFalse(self.donor.is_available)

        send_email.assert_called_once()
        _, kwargs = send_email.call_args
        self.assertEqual(kwargs["to_emails"], ["donor@example.com"])
        self.assertEqual(kwargs["text_template"], "emails/donor/removed-redirection-ngo/main.txt")
        self.assertEqual(kwargs["html_template"], "emails/donor/removed-redirection-ngo/main.html")
        self.assertEqual(
            kwargs["context"],
            {
                "cause_name": "Test Cause",
                "action_url": "https://example.com/action",
                "site_title": "site",
            },
        )

        expected_action_url = reverse("twopercent", kwargs={"cause_slug": self.cause.slug})
        build_uri.assert_called_once_with(expected_action_url)
        extend_email_context.assert_called_once_with()

    @patch("donations.views.ngo_account.redirections.extend_email_context", return_value={"site_title": "site"})
    @patch("donations.views.ngo_account.redirections.build_uri", return_value="https://example.com/home")
    @patch("donations.views.ngo_account.redirections.send_email")
    def test_post_disables_redirection_and_notifies_without_cause(
        self,
        send_email,
        build_uri,
        extend_email_context,
    ):
        donor = Donor.objects.create(
            ngo=self.ngo,
            cause=None,
            email="nocause@example.com",
            has_signed=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("my-organization:redirection-disable", args=[donor.pk]),
            {"disable_redirection": "true"},
        )

        self.assertRedirects(response, reverse("my-organization:redirections"))
        donor.refresh_from_db()
        self.assertFalse(donor.is_available)

        send_email.assert_called_once()
        __, kwargs = send_email.call_args
        self.assertEqual(kwargs["to_emails"], ["nocause@example.com"])
        self.assertEqual(
            kwargs["context"],
            {
                "cause_name": _("<Cause no longer available>"),
                "action_url": "https://example.com/home",
                "site_title": "site",
            },
        )
        expected_action_url = reverse("home")
        build_uri.assert_called_once_with(expected_action_url)
        extend_email_context.assert_called_once_with()
