variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "asrserve"
}

variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "container_image" {
  description = "Full ECR image URI:tag, set by CI after build_and_push.sh"
  type        = string
}

variable "task_cpu" {
  type    = number
  default = 1024
}

variable "task_memory" {
  type    = number
  default = 3072
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "openai_api_key_secret_arn" {
  description = "ARN of a Secrets Manager secret holding OPENAI_API_KEY -- never plaintext in tfvars"
  type        = string
}

variable "anthropic_api_key_secret_arn" {
  description = "ARN of a Secrets Manager secret holding ANTHROPIC_API_KEY -- never plaintext in tfvars"
  type        = string
}
