resource "aws_cloudfront_distribution" "main" {
  price_class     = "PriceClass_100"
  enabled         = true
  is_ipv6_enabled = true
  http_version    = "http2and3"
  aliases         = local.domains

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = aws_lb.main.dns_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name              = module.s3_public.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
    origin_id                = module.s3_public.id
  }

  origin {
    domain_name              = module.s3_static.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
    origin_id                = module.s3_static.id
  }

  # Static
  ordered_cache_behavior {
    path_pattern               = "/static/*"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = module.s3_static.id
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" #Managed-CachingOptimized
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" #Managed-CORS-S3Origin
    response_headers_policy_id = "eaab4381-ed33-4a86-88ca-d9558dc6cd63" #Managed-CORS-with-preflight-and-SecurityHeadersPolicy
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.www_redirect.arn
    }
  }

  # Media
  ordered_cache_behavior {
    path_pattern               = "/media/*"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = module.s3_public.id
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" #Managed-CachingOptimized
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" #Managed-CORS-S3Origin
    response_headers_policy_id = "eaab4381-ed33-4a86-88ca-d9558dc6cd63" #Managed-CORS-with-preflight-and-SecurityHeadersPolicy
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.www_redirect.arn
    }
  }

  # Sample forms
  ordered_cache_behavior {
    path_pattern               = "/ngo-forms/*"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = module.s3_public.id
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" #Managed-CachingOptimized
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" #Managed-CORS-S3Origin
    response_headers_policy_id = "eaab4381-ed33-4a86-88ca-d9558dc6cd63" #Managed-CORS-with-preflight-and-SecurityHeadersPolicy
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.www_redirect.arn
    }
  }

  # Logged in container
  dynamic "ordered_cache_behavior" {
    for_each = [
      "/api/*",
      "/cron/*",
      "/verify/*",
      "/admin/*",
      "/login/*",
      "/ong/*",
      "/password/*",
      "/forgot/*",
      "/contul-meu/*",
      "/date-cont/*",
      "/asociatia/*",
      "/*/semnatura/",
      "/*/succes/",
    ]

    content {
      path_pattern               = ordered_cache_behavior.value
      allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      cached_methods             = ["GET", "HEAD", "OPTIONS"]
      target_origin_id           = aws_lb.main.dns_name
      cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" #Managed-CachingDisabled
      origin_request_policy_id   = "33f36d7e-f396-46d9-90e0-52428a34d9dc" #Managed-AllViewerAndCloudFrontHeaders-2022-06
      response_headers_policy_id = "67f7725c-6f97-4210-82d7-5512b31e9d03" #Managed-SecurityHeadersPolicy
      viewer_protocol_policy     = "redirect-to-https"
      compress                   = true

      function_association {
        event_type   = "viewer-request"
        function_arn = aws_cloudfront_function.www_redirect.arn
      }
    }
  }

  # Public Container
  default_cache_behavior {
    allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    target_origin_id           = aws_lb.main.dns_name
    cache_policy_id            = aws_cloudfront_cache_policy.default.id
    origin_request_policy_id   = "33f36d7e-f396-46d9-90e0-52428a34d9dc" #Managed-AllViewerAndCloudFrontHeaders-2022-06
    response_headers_policy_id = "67f7725c-6f97-4210-82d7-5512b31e9d03" #Managed-SecurityHeadersPolicy
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.www_redirect.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

resource "aws_cloudfront_cache_policy" "default" {
  name        = "${local.namespace}-cache-policy"
  min_ttl     = 1
  default_ttl = 60
  max_ttl     = 300

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"

      headers {
        items = [
          "Host",
        ]
      }
    }

    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

resource "aws_cloudfront_origin_request_policy" "default" {
  name = "${local.namespace}-origin-request-policy"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "allViewerAndWhitelistCloudFront"

    headers {
      items = [
        "CloudFront-Forwarded-Proto",
      ]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = module.s3_public.id
  description                       = ""
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_function" "www_redirect" {
  name    = "${local.namespace}-www-redirect"
  runtime = "cloudfront-js-1.0"
  comment = "Redirects www.${var.domain_name} to ${var.domain_name}"
  publish = true
  code    = file("${path.module}/functions/www-redirect.js")
}
