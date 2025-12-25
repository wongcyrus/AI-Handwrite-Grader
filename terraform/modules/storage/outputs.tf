output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "connection_string" {
  description = "Connection string for the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "blob_endpoint" {
  description = "Blob endpoint URL"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "table_endpoint" {
  description = "Table endpoint URL"
  value       = azurerm_storage_account.main.primary_table_endpoint
}
