# Domain
resource "aws_sesv2_email_identity" "main" {
  email_identity         = var.domain_name
  configuration_set_name = aws_sesv2_configuration_set.main.configuration_set_name
}

# Configuration set
resource "aws_sesv2_configuration_set" "main" {
  configuration_set_name = local.namespace

  delivery_options {
    tls_policy = "REQUIRE"
  }

  sending_options {
    sending_enabled = true
  }

  reputation_options {
    reputation_metrics_enabled = true
  }
}

# DMARC
resource "aws_route53_record" "txt_dmarc" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_dmarc.${aws_sesv2_email_identity.main.email_identity}"
  type    = "TXT"
  ttl     = "600"
  records = ["v=DMARC1; p=quarantine;"]
}

# MAIL FROM
resource "aws_sesv2_email_identity_mail_from_attributes" "main" {
  email_identity         = aws_sesv2_email_identity.main.email_identity
  mail_from_domain       = "mail.${aws_sesv2_email_identity.main.email_identity}"
  behavior_on_mx_failure = "REJECT_MESSAGE"
}

resource "aws_route53_record" "mail_from_mx" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "mail.${aws_sesv2_email_identity.main.email_identity}"
  type    = "MX"
  ttl     = "300"
  records = ["10 feedback-smtp.${var.region}.amazonses.com"]
}

resource "aws_route53_record" "mail_from_spf" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "mail.${aws_sesv2_email_identity.main.email_identity}"
  type    = "TXT"
  ttl     = "300"
  records = ["v=spf1 include:amazonses.com include:_spf.google.com include:sendgrid.net ~all"]
}


# DKIM
resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${element(aws_sesv2_email_identity.main.dkim_signing_attributes[0].tokens, count.index)}._domainkey.${aws_sesv2_email_identity.main.email_identity}"
  type    = "CNAME"
  ttl     = "600"
  records = ["${element(aws_sesv2_email_identity.main.dkim_signing_attributes[0].tokens, count.index)}.dkim.amazonses.com"]
}
