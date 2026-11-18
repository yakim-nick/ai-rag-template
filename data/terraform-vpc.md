# Creating a VPC with Terraform

A Virtual Private Cloud (VPC) is an isolated virtual network in AWS. With Terraform
you declare it with the `aws_vpc` resource.

## Minimal example

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "main-vpc"
  }
}
```

- `cidr_block` is required. It sets the private IP range of the VPC (here 65,536 addresses).
- `enable_dns_support` and `enable_dns_hostnames` control DNS resolution inside the VPC.
- `tags` help you find and organise resources in the AWS console.

## Subnets

A VPC is divided into subnets. Each `aws_subnet` needs the VPC id and its own CIDR
block, which must be a subset of the VPC range:

```hcl
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-south-1a"
}
```

## Applying

Run `terraform init`, then `terraform plan` to preview, then `terraform apply`.
