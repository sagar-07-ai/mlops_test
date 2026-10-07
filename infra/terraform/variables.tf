variable "aws_region" {
  description = "AWS region where infrastructure will be deployed"
  type        = string
}

variable "project_name" {
  description = "Name used to identify resources belonging to this project"
  type        = string
  default     = "mlops-test"
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either dev or prod."
  }
}
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "Public subnet definitions"

  type = map(object({
    cidr = string
    az   = string
  }))

  default = {
    public-a = {
      cidr = "10.0.1.0/24"
      az   = "ap-south-1a"
    }

    public-b = {
      cidr = "10.0.2.0/24"
      az   = "ap-south-1b"
    }
  }
}

variable "private_subnets" {
  description = "Private subnet definitions"

  type = map(object({
    cidr = string
    az   = string
  }))

  default = {
    private-a = {
      cidr = "10.0.11.0/24"
      az   = "ap-south-1a"
    }

    private-b = {
      cidr = "10.0.12.0/24"
      az   = "ap-south-1b"
    }
  }
}