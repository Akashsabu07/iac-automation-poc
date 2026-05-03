output "resource_group_id" {
  description = "The ID of the Azure Resource Group."
  value       = azurerm_resource_group.rg.id
}

output "resource_group_name" {
  description = "The name of the Azure Resource Group."
  value       = azurerm_resource_group.rg.name
}

output "storage_account_id" {
  description = "The ID of the Azure Storage Account."
  value       = azurerm_storage_account.sa.id
}

output "storage_account_name" {
  description = "The name of the Azure Storage Account."
  value       = azurerm_storage_account.sa.name
}

output "storage_account_primary_blob_endpoint" {
  description = "The primary blob endpoint of the Azure Storage Account."
  value       = azurerm_storage_account.sa.primary_blob_endpoint
}

output "storage_account_primary_connection_string" {
  description = "The primary connection string for the Azure Storage Account."
  value       = azurerm_storage_account.sa.primary_connection_string
  sensitive   = true
}