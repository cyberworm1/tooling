provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "media-assets-rg"
  location = "East US"
}

resource "azurerm_storage_account" "storage" {
  name                     = "gameassetsstorage${random_string.random.id}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant for media IP protection
  enable_https_traffic_only = true
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false  # Enforce private access

  blob_properties {
    delete_retention_policy {
      days = 7  # Soft-delete for accidental asset loss
    }
  }
}

resource "azurerm_storage_container" "container" {
  name                  = "game-assets"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

resource "random_string" "random" {
  length  = 6
  special = false
  upper   = false
}

output "storage_account_name" {
  value = azurerm_storage_account.storage.name
}