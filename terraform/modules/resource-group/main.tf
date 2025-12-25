resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.location
  tags     = var.tags
}

resource "azurerm_user_assigned_identity" "main" {
  name                = "${var.project_name}-${var.environment}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  tags               = var.tags
}
