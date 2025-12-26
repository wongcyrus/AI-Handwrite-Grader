terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 1.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  subscription_id = "37466f89-c009-41b3-9d2c-b832f29b74da"
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Variables
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-handwrite-grader"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Random string for unique naming
resource "random_string" "storage_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Local values for common tags
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Resource Group Module
module "resource_group" {
  source = "./modules/resource-group"
  
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = "${var.project_name}-${var.environment}-rg"
  tags                = local.common_tags
}

# Storage Module
module "storage" {
  source = "./modules/storage"
  
  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.resource_group.name
  location           = var.location
  tags               = local.common_tags
}

# Key Vault Module
module "key_vault" {
  source = "./modules/key-vault"
  
  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.resource_group.name
  location           = var.location
  tags               = local.common_tags
}

# AI Foundry Module
module "ai_foundry" {
  source = "./modules/ai-foundry"
  
  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.resource_group.name
  location           = var.location
  storage_account_id  = module.storage.storage_account_id
  key_vault_id        = module.key_vault.key_vault_id
  tags               = local.common_tags
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${replace(var.project_name, "-", "")}${var.environment}acr"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = local.common_tags
}

# Build and push Docker image
resource "null_resource" "docker_build" {
  depends_on = [azurerm_container_registry.main]
  
  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.root}/..
      az acr login --name ${azurerm_container_registry.main.name}
      docker build -t ${azurerm_container_registry.main.login_server}/ai-handwrite-grader:latest .
      docker push ${azurerm_container_registry.main.login_server}/ai-handwrite-grader:latest
    EOT
  }
  
  triggers = {
    dockerfile_hash = filemd5("${path.root}/../Dockerfile")
    app_hash = sha1(join("", [for f in fileset("${path.root}/../app", "**") : filesha1("${path.root}/../app/${f}")]))
  }
}

# Container Instance
resource "azurerm_container_group" "main" {
  depends_on = [null_resource.docker_build]
  
  name                = "${var.project_name}-${var.environment}-aci"
  location            = var.location
  resource_group_name = module.resource_group.name
  ip_address_type     = "Public"
  dns_name_label      = "${var.project_name}-${var.environment}-${random_string.storage_suffix.result}"
  os_type             = "Linux"

  container {
    name   = "ai-handwrite-grader"
    image  = "${azurerm_container_registry.main.login_server}/ai-handwrite-grader:latest"
    cpu    = "1.0"
    memory = "2.0"

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      FLASK_ENV                        = "production"
      AZURE_STORAGE_CONNECTION_STRING  = module.storage.connection_string
      AZURE_AI_PROJECT_ENDPOINT        = module.ai_foundry.ai_foundry_project_endpoint
      AZURE_AI_MODEL_DEPLOYMENT_NAME   = "gpt-52-chat"
      OPENAI_API_VERSION               = "2024-05-13"
      # Agent IDs will be populated after deployment
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  tags = local.common_tags
}

# Outputs
output "resource_group_name" {
  value = module.resource_group.name
}

output "storage_account_name" {
  value = module.storage.storage_account_name
}

output "storage_connection_string" {
  value     = module.storage.connection_string
  sensitive = true
}

output "container_registry_name" {
  value = azurerm_container_registry.main.name
}

output "container_registry_server" {
  value = azurerm_container_registry.main.login_server
}

output "container_registry_username" {
  value = azurerm_container_registry.main.admin_username
}

output "container_registry_password" {
  value     = azurerm_container_registry.main.admin_password
  sensitive = true
}

output "container_instance_fqdn" {
  value = azurerm_container_group.main.fqdn
}

output "container_instance_ip" {
  value = azurerm_container_group.main.ip_address
}

output "ai_foundry_hub_id" {
  value = module.ai_foundry.ai_foundry_id
}

output "ai_foundry_project_id" {
  value = module.ai_foundry.ai_project_id
}

output "ai_foundry_endpoint" {
  value = module.ai_foundry.ai_services_endpoint
}

output "ai_foundry_key" {
  value     = module.ai_foundry.ai_services_key
  sensitive = true
}
