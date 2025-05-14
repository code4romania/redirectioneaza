from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse


class AnimalTestCase(TestCase):
    def setUp(self):
        self.client = Client(http_host=settings.APEX_DOMAIN)

    def test_nothing(self):
        response = self.client.get(reverse("twopercent"), args=["non-existing-ngo"])
        self.assertEqual(response.status_code, 200)
