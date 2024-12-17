variable "env" {
  description = "Environment"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["production", "staging", "development"], var.env)
    error_message = "Allowed values for env are \"production\", \"staging\" or \"development\"."
  }
}

variable "region" {
  description = "Region"
  type        = string
  default     = "eu-central-1"
}

variable "domain_name" {
  description = "Domain name used by the application. Must belong to the Route 53 zone defined in `route_53_zone_id`."
  type        = string
}

variable "route_53_zone_id" {
  type = string
}

variable "bastion_public_key" {
  description = "Public SSH key used to connect to the bastion"
  type        = string
}

variable "seed_admin_email" {
  description = "Initial administrator email"
  type        = string
}

variable "seed_admin_password" {
  description = "Initial administrator password"
  type        = string
}

variable "sentry_dsn" {
  description = "Sentry DSN"
  type        = string
  default     = null
}

variable "use_load_balancer" {
  type    = bool
  default = true
}

variable "create_iam_service_linked_role" {
  description = "Whether to create `AWSServiceRoleForECS` service-linked role. Set it to `false` if you already have an ECS cluster created in the AWS account and AWSServiceRoleForECS already exists."
  type        = bool
  default     = true
}

variable "enable_execute_command" {
  description = "Enable aws ecs execute_command"
  type        = bool
  default     = false
}

variable "google_analytics_id" {
  type    = string
  default = null
}

variable "recaptcha_required_score" {
  type    = number
  default = 0.5
}

variable "recaptcha_public_key" {
  type    = string
  default = null
}

variable "recaptcha_private_key" {
  type      = string
  sensitive = true
  default   = null
}

# Cognito authentication
variable "aws_cognito_region" {
  type    = string
  default = null
}

variable "aws_cognito_domain" {
  type    = string
  default = null
}

variable "aws_cognito_user_pool_id" {
  type    = string
  default = null
}

variable "aws_cognito_client_id" {
  type    = string
  default = null
}

variable "aws_cognito_client_secret" {
  type      = string
  sensitive = true
  default   = null
}

# NGO Hub API
variable "ngohub_api_account" {
  type    = string
  default = null
}

variable "ngohub_api_key" {
  type      = string
  sensitive = true
  default   = null
}

