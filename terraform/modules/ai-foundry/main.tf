terraform {
  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 1.0"
    }
  }
}

# Create AI Services with project management enabled using AzAPI
resource "azapi_resource" "ai_services" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "${var.project_name}-${var.environment}-ai"
  parent_id                 = var.resource_group_id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      # Support both Entra ID and API Key authentication
      disableLocalAuth = false
      
      # Enable project management for AI Foundry
      allowProjectManagement = true
      
      # Set custom subdomain name
      customSubDomainName = "${replace(var.project_name, "-", "")}${var.environment}ai"
    }
  }
  
  tags = var.tags
}

resource "azapi_resource" "gpt5_deployment" {
  type                      = "Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview"
  name                      = "gpt-5-chat"
  parent_id                 = azapi_resource.ai_services.id
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

# Create AI Foundry project as child resource using AzAPI
resource "azapi_resource" "ai_foundry_project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "${var.project_name}-${var.environment}-proj"
  parent_id                 = azapi_resource.ai_services.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "${var.project_name}-${var.environment}-proj"
      description = "AI Handwrite Grader Project"
    }
  }
  
  depends_on = [azapi_resource.ai_services]
}

# Deploy agents after infrastructure is ready
resource "null_resource" "deploy_agents" {
  depends_on = [
    azapi_resource.ai_foundry_project,
    azapi_resource.gpt5_deployment
  ]

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.root}/..
      source venv/bin/activate
      python deploy_agents_tf.py
    EOT
  }

  # Cleanup nested resources before destroy
  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      /bin/bash -c "az resource list --resource-group 'ai-handwrite-grader-dev-rg' --resource-type 'Microsoft.CognitiveServices/accounts/projects' --query '[].id' -o tsv | while read project_id; do
        if [ ! -z \"\$project_id\" ]; then
          echo \"Deleting nested project: \$project_id\"
          az resource delete --ids \"\$project_id\" || true
        fi
      done"
    EOT
  }

  triggers = {
    project_endpoint = azapi_resource.ai_foundry_project.id
    model_deployment = azapi_resource.gpt5_deployment.id
    # Only re-run if agents don't exist
    run_once = "agents_v1"
  }
}
