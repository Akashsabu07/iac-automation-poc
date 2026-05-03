variable "resource_group_name" {
  description = "Name of the Azure Resource Group."
  type        = string
  default     = "rg-iac-poc-test-001"

  validation {
    condition     = startswith(var.resource_group_name, "rg-")
    error_message = "Resource group name must start with 'rg-'."
  }
}

variable "location" {
  description = "Azure region where resources will be deployed."
  type        = string
  default     = "westus2"

  validation {
    condition     = contains(["eastus", "eastus2", "westus", "westus2", "centralus", "westeurope", "northeurope"], var.location)
    error_message = "Location must be one of the allowed Azure regions: eastus, eastus2, westus, westus2, centralus, westeurope, northeurope."
  }
}

variable "storage_account_name" {
  description = "Name of the Azure Storage Account."
  type        = string
  default     = "stiacpoctest001"

  validation {
    condition     = length(var.storage_account_name) >= 3 && length(var.storage_account_name) <= 24 && can(regex("^[a-z0-9]+$", var.storage_account_name))
    error_message = "Storage account name must be 3-24 lowercase letters and digits only."
  }
}

variable "replication_type" {
  description = "Replication type for the Azure Storage Account."
  type        = string
  default     = "GRS"

  validation {
    condition     = contains(["LRS", "GRS", "ZRS", "RAGRS"], var.replication_type)
    error_message = "Replication type must be one of LRS, GRS, ZRS, or RAGRS."
  }
}

variable "tags" {
  description = "A map of tags to assign to resources."
  type        = map(string)
  default = {
    owner     = "akash"
    project   = "iac-automation-poc"
    env       = "test"
    security  = "hardened"
  }
}