output "resource_group_id" {
  description = "The ID of the Azure Resource Group."
  value       = azurerm_resource_group.rg.id
}

output "storage_account_id" {
  description = "The ID of the Azure Storage Account."
  value       = azurerm_storage_account.sa.id
}

output "storage_account_primary_blob_endpoint" {
  description = "The primary blob endpoint for the Azure Storage Account."
  value       = azurerm_storage_account.sa.primary_blob_endpoint
}