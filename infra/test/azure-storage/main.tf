terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group."
  type        = string
  default     = "rg-iac-poc-test-001"
}

variable "location" {
  description = "Azure region for the resources."
  type        = string
  default     = "westus2"
}

variable "storage_account_name" {
  description = "Name of the Azure Storage Account."
  type        = string
  default     = "stiacpoctest001"
}

variable "replication_type" {
  description = "Replication type for the Storage Account (e.g., GRS, LRS, ZRS)."
  type        = string
  default     = "GRS"
}

variable "tags" {
  description = "A map of tags to assign to the resources."
  type        = map(string)
  default = {
    owner     = "akash"
    project   = "iac-automation-poc"
    env       = "test"
    security  = "hardened"
  }
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "sa" {
  name                            = var.storage_account_name
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = azurerm_resource_group.rg.location
  account_tier                    = "Standard"
  account_replication_type        = var.replication_type
  min_tls_version                 = "TLS1_2"
  enable_https_traffic_only       = true
  public_network_access_enabled   = false
  account_kind                    = "StorageV2"
  infrastructure_encryption_enabled = true
  tags                            = var.tags

  blob_properties {
    versioning_enabled = true
  }
}