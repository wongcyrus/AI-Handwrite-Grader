resource "azurerm_key_vault" "key_vault" {
  name                = "kv-${var.environment}-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  
  sku_name                 = "standard"
  purge_protection_enabled = true
  
  tags = var.tags
}

resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.key_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id
  
  key_permissions = [
    "Create",
    "Get",
    "Delete",
    "Purge",
    "GetRotationPolicy",
  ]
}

resource "random_string" "suffix" {
  length  = 8
  lower   = true
  numeric = false
  special = false
  upper   = false
}

data "azurerm_client_config" "current" {}
