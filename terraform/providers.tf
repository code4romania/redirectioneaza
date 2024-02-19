terraform {
  required_version = "~> 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.16"
    }
  }

  cloud {
    organization = "code4romania"

    workspaces {
      name    = "redirectioneaza-production"
      project = "redirectioneaza"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      app = "redirectioneaza"
      env = var.env
    }
  }
}

provider "aws" {
  alias  = "acm"
  region = "us-east-1"

  default_tags {
    tags = {
      app = "redirectioneaza"
      env = var.env
    }
  }
}
