variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-grader"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "container_cpu" {
  description = "CPU allocation for container"
  type        = string
  default     = "0.5"
}

variable "container_memory" {
  description = "Memory allocation for container"
  type        = string
  default     = "1.5"
}

variable "auto_shutdown_enabled" {
  description = "Enable auto-shutdown for cost optimization"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    Project     = "AI-Handwriting-Grader"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
