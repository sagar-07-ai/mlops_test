output "project_name" {
  description = "Project name used by Terraform"
  value       = var.project_name
}

output "environment" {
  description = "Current infrastructure environment"
  value       = var.environment
}

output "name_prefix" {
  description = "Naming prefix used for infrastructure resources"
  value       = local.name_prefix
}
output "ecr_repository_url" {
  description = "ECR repository URL for the application image"
  value       = aws_ecr_repository.app.repository_url
}