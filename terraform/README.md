# terraform instructions

1. Go to [ECS Account settings](https://eu-central-1.console.aws.amazon.com/ecs/v2/account-settings?region=eu-central-1) for the region you're deploying in and make sure AWSVPC Trunking is turned on.

2. Replace the backend configuration in `providers.tf` with your own bucket name, key and region.

3. Configure the required variables from `variables.tf`. If you've ever created a cluster in this AWS account, make sure to set the `create_iam_service_linked_role` to false.

Example configuration:
```
route_53_zone_id               = "Z1Q2W3E4R5T6Y7"
domain_name                    = "test.example.com"
bastion_public_key             = "ssh-ed25519 AAAAC3NzaC1lZD..."
seed_admin_email               = "test@example.com"
seed_admin_password            = "super_secure_random_password"
create_iam_service_linked_role = false
```

4. Run `terraform apply` and wait for the cluster to be created.

5. Once everything is done, you should be able to login at `https://[domain_name]/staff/users/login/` using the `seed_admin_email` and `seed_admin_password` you've configured.
