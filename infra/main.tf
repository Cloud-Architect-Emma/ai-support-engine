terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "lambda" {
  source = "./lambda"
}

module "api_gateway" {
  source      = "./api_gateway"
  lambda_arn  = module.lambda.lambda_arn
}

module "dynamodb" {
  source = "./dynamodb"
}
