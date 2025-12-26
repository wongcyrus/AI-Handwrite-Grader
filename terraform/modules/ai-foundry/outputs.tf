output "ai_foundry_id" {
  description = "AI Foundry hub ID"
  value       = azurerm_ai_foundry.ai_foundry.id
}

output "ai_project_id" {
  description = "AI Foundry project ID"
  value       = azurerm_ai_foundry_project.ai_project.id
}

output "ai_services_endpoint" {
  description = "AI Services endpoint"
  value       = azurerm_ai_services.ai_services.endpoint
}

output "ai_services_key" {
  description = "AI Services primary key"
  value       = azurerm_ai_services.ai_services.primary_access_key
  sensitive   = true
}

output "ai_foundry_project_endpoint" {
  description = "AI Foundry project endpoint"
  value       = "https://${azurerm_ai_services.ai_services.custom_subdomain_name}.services.ai.azure.com/api/projects/${var.project_name}-${var.environment}-project"
}

output "agent_deployment_status" {
  description = "Agent deployment completion status"
  value       = null_resource.deploy_agents.id
}
