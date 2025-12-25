output "endpoint" {
  description = "AI Foundry endpoint"
  value       = azurerm_cognitive_account.ai_foundry.endpoint
}

output "key" {
  description = "AI Foundry primary key"
  value       = azurerm_cognitive_account.ai_foundry.primary_access_key
  sensitive   = true
}

output "document_intelligence_endpoint" {
  description = "Document Intelligence endpoint"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}

output "document_intelligence_key" {
  description = "Document Intelligence primary key"
  value       = azurerm_cognitive_account.document_intelligence.primary_access_key
  sensitive   = true
}
