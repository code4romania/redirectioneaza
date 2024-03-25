import pytest

from ..middleware import InvalidSubdomain, PartnerDomainMiddleware


@pytest.mark.parametrize(
    "apex, subdomain, expected",
    [
        ("example.com", "test1.example.com", "test1"),
        ("example.com", "TesT1.exaMpLe.com", "test1"),
        ("example.com", "exAmple.com", ""),
    ],
)
def test_partner_domain_middleware_extraction(apex, subdomain, expected):
    subdomain = PartnerDomainMiddleware.extract_subdomain(subdomain, apex)
    assert subdomain == expected


def test_invalid_subdomain():
    with pytest.raises(InvalidSubdomain):
        PartnerDomainMiddleware.extract_subdomain("test1.example.ORG", "example.com")
