from django.test import TestCase

from .middleware import PartnerDomainMiddleware, InvalidSubdomain


class PartnerDomainMiddlewareTestCase(TestCase):
    def setUp(self):
        self.apex = "example.com"

    def test_subdomain(self):
        # Test standard subdomain extraction
        subdom1 = PartnerDomainMiddleware.extract_subdomain("test1.example.com", self.apex)
        self.assertEqual(subdom1, "test1")

        # Test various capitalization subdomain extraction
        subdom2 = PartnerDomainMiddleware.extract_subdomain("TesT1.exaMpLe.com", self.apex)
        self.assertEqual(subdom2, "test1")

        # Test apex domain
        subdom3 = PartnerDomainMiddleware.extract_subdomain("exAmple.com", self.apex)
        self.assertEqual(subdom3, "")

        # Test invalid subdomain
        self.assertRaises(InvalidSubdomain, PartnerDomainMiddleware.extract_subdomain, "test1.example.ORG", self.apex)
