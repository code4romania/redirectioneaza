resource "aws_eip" "nat_gateway" {
  domain = "vpc"
  tags = {
    Name = "${local.namespace}-nat-gateway"
  }
}
