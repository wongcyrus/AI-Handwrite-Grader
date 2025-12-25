terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstateaigrader"
    container_name      = "tfstate"
    key                 = "dev.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

module "resource_group" {
  source = "../../modules/resource-group"
  
  project_name = var.project_name
  environment  = var.environment
  location     = var.location
  tags         = var.tags
}

module "storage" {
  source = "../../modules/storage"
  
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.resource_group.name
  tags                = var.tags
}

module "ai_foundry" {
  source = "../../modules/ai-foundry"
  
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.resource_group.name
  tags                = var.tags
}

module "container_registry" {
  source = "../../modules/container-registry"
  
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.resource_group.name
  tags                = var.tags
}

module "container_instances" {
  source = "../../modules/container-instances"
  
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.resource_group.name
  
  storage_connection_string = module.storage.connection_string
  ai_foundry_endpoint      = module.ai_foundry.endpoint
  container_registry_server = module.container_registry.login_server
  
  auto_shutdown_enabled = var.auto_shutdown_enabled
  container_cpu        = var.container_cpu
  container_memory     = var.container_memory
  
  tags = var.tags
}
