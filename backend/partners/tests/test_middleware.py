from django.test import TestCase

from partners.middleware import InvalidSubdomain, PartnerDomainMiddleware


class PartnerMiddlewareTests(TestCase):
    def setUp(self):
        pass

    def test_partner_domain_middleware_extraction(self):
        apex = "example.com"
        self.assertEqual("test1", PartnerDomainMiddleware.extract_subdomain("test1.example.com", apex))
        self.assertEqual("test1", PartnerDomainMiddleware.extract_subdomain("test1.exaMpLe.com", apex))
        self.assertEqual("", PartnerDomainMiddleware.extract_subdomain("exAmple.com", apex))

    def test_invalid_subdomain(self):
        self.assertRaises(
            InvalidSubdomain, PartnerDomainMiddleware.extract_subdomain, "test1.example.ORG", "example.com"
        )
