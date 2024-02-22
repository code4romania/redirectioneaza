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

variable "donations_limit" {
  description = "The final date for donations"
  type        = string
}

variable "donations_limit_to_current_year" {
  description = "The final date for donations will be set to use the current year"
  type        = bool
  default     = true
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

variable "old_session_key" {
  description = "Old session key"
  type        = string
  default     = null
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
  type    = string
  default = null
}
