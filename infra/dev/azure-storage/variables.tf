variable "resource_group_name" {
  description = "Name of the Azure Resource Group."
  type        = string
  default     = "rg-iac-poc-dev-001"
}

variable "location" {
  description = "Azure region where resources will be deployed."
  type        = string
  default     = "eastus"
}

variable "storage_account_name" {
  description = "Name of the Azure Storage Account."
  type        = string
  default     = "stiacpocdev001"
}

variable "replication_type" {
  description = "Replication type for the Azure Storage Account (e.g., LRS, GRS, RAGRS, ZRS)."
  type        = string
  default     = "LRS"
}

variable "tags" {
  description = "A map of tags to assign to all resources."
  type        = map(string)
  default = {
    owner   = "akash"
    project = "iac-automation-poc"
    env     = "dev"
  }
}