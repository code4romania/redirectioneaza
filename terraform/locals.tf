locals {
  namespace  = "redirectioneaza-${var.env}"
  image_repo = "code4romania/redirectioneaza"
  image_tag  = "3.4.7"

  availability_zone = data.aws_availability_zones.current.names[0]

  domains = [
    var.domain_name,
    "*.${var.domain_name}",
  ]

  ecs = {
    instance_types = {
      "m5.large"  = ""
      "m5a.large" = ""
    }
  }

  db = {
    name           = "redirectioneaza"
    instance_class = var.env == "production" ? "db.t4g.medium" : "db.t4g.micro"
  }

  networking = {
    cidr_block = "10.0.0.0/16"

    public_subnets = [
      "10.0.1.0/24",
      "10.0.2.0/24",
      "10.0.3.0/24"
    ]

    private_subnets = [
      "10.0.4.0/24",
      "10.0.5.0/24",
      "10.0.6.0/24"
    ]
  }
}
