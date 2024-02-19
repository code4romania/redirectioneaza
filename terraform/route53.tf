# A record
resource "aws_route53_record" "ipv4" {
  count = length(local.domains)

  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.domains[count.index]
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = true
  }
}

# AAAA record
resource "aws_route53_record" "ipv6" {
  count = length(local.domains)

  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.domains[count.index]
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = true
  }
}
