terraform {
  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 1.0"
    }
  }
}

resource "azurerm_ai_services" "ai_services" {
  name                  = "${var.project_name}-${var.environment}-ai"
  resource_group_name   = var.resource_group_name
  location             = "East US 2"
  sku_name             = "S0"
  custom_subdomain_name = "${replace(var.project_name, "-", "")}${var.environment}ai"
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

resource "azapi_resource" "gpt5_deployment" {
  type                      = "Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview"
  name                      = "gpt-5-chat"
  parent_id                 = azurerm_ai_services.ai_services.id
  schema_validation_enabled = false

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 50
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-5-chat"
        version = "2025-10-03"
      }
      raiPolicyName = "Microsoft.DefaultV2"
    }
  }
}

resource "azurerm_ai_foundry" "ai_foundry" {
  name                = "${var.project_name}-${var.environment}-hub"
  resource_group_name = var.resource_group_name
  location           = var.location
  storage_account_id  = var.storage_account_id
  key_vault_id        = var.key_vault_id
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

resource "azurerm_ai_foundry_project" "ai_project" {
  name               = "${var.project_name}-${var.environment}-proj"
  location          = azurerm_ai_foundry.ai_foundry.location
  ai_services_hub_id = azurerm_ai_foundry.ai_foundry.id
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Connect AI Services to the project using role assignment
resource "azurerm_role_assignment" "ai_services_connection" {
  scope                = azurerm_ai_foundry_project.ai_project.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_ai_foundry_project.ai_project.identity[0].principal_id
}

resource "azurerm_role_assignment" "ai_services_contributor" {
  scope                = azurerm_ai_services.ai_services.id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = azurerm_ai_foundry_project.ai_project.identity[0].principal_id
}

# Deploy agents after infrastructure is ready
resource "null_resource" "deploy_agents" {
  depends_on = [
    azurerm_ai_foundry_project.ai_project,
    azapi_resource.gpt5_deployment
  ]

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.root}/..
      source venv/bin/activate
      export AZURE_AI_PROJECT_ENDPOINT="https://${azurerm_ai_services.ai_services.custom_subdomain_name}.services.ai.azure.com/api/projects/${var.project_name}-${var.environment}-project"
      python deploy_agents_tf.py
    EOT
  }

  triggers = {
    project_endpoint = "https://${azurerm_ai_services.ai_services.custom_subdomain_name}.services.ai.azure.com/api/projects/${var.project_name}-${var.environment}-project"
    model_deployment = azapi_resource.gpt5_deployment.id
    # Only re-run if agents don't exist
    run_once = "agents_v1"
  }
}
