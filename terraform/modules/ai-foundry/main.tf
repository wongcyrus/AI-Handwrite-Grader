resource "azurerm_cognitive_account" "ai_foundry" {
  name                = "${var.project_name}-${var.environment}-ai-foundry"
  resource_group_name = var.resource_group_name
  location           = var.location
  kind               = "AIServices"
  sku_name           = "S0"
  
  tags = var.tags
}

resource "azurerm_cognitive_account" "document_intelligence" {
  name                = "${var.project_name}-${var.environment}-doc-intel"
  resource_group_name = var.resource_group_name
  location           = var.location
  kind               = "FormRecognizer"
  sku_name           = "S0"
  
  tags = var.tags
}
