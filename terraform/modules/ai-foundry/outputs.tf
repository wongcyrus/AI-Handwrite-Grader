output "ai_foundry_id" {
  description = "AI Services resource ID (acts as hub)"
  value       = azapi_resource.ai_services.id
}

output "ai_project_id" {
  description = "AI Foundry project ID"
  value       = azapi_resource.ai_foundry_project.id
}

output "ai_services_endpoint" {
  description = "AI Services endpoint"
  value       = "https://aihandwritegraderdevai.cognitiveservices.azure.com/"
}

output "ai_services_key" {
  description = "AI Services primary key"
  value       = "placeholder-key"
  sensitive   = true
}

output "ai_foundry_project_endpoint" {
  description = "AI Foundry project endpoint"
  value       = "https://aihandwritegraderdevai.cognitiveservices.azure.com/"
}

output "agent_deployment_status" {
  description = "Agent deployment completion status"
  value       = null_resource.deploy_agents.id
}
