resource "azurerm_storage_account" "main" {
  name                     = "aigrader${var.environment}${substr(md5("${var.project_name}-${var.environment}"), 0, 8)}"
  resource_group_name      = var.resource_group_name
  location                = var.location
  account_tier            = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    delete_retention_policy {
      days = 7
    }
  }
  
  tags = var.tags
}

resource "azurerm_storage_container" "pdfs" {
  name                 = "pdfs"
  storage_account_id   = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "images" {
  name                 = "images"
  storage_account_id   = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "results" {
  name                 = "results"
  storage_account_id   = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_table" "projects" {
  name                 = "projects"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_table" "annotations" {
  name                 = "annotations"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_table" "scoring" {
  name                 = "scoring"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_table" "users" {
  name                 = "users"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_table" "auditlog" {
  name                 = "auditlog"
  storage_account_name = azurerm_storage_account.main.name
}
