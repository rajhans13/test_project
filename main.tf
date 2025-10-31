terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.102"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_resource_group" "target" {
  name = var.resource_group_name
}

data "azurerm_key_vault" "secrets" {
  name                = var.key_vault_name
  resource_group_name = var.key_vault_resource_group
}

data "azurerm_key_vault_secret" "local_admin_password" {
  name         = var.admin_password_secret_name
  key_vault_id = data.azurerm_key_vault.secrets.id
}

module "network" {
  source = "./modules/network"

  location            = data.azurerm_resource_group.target.location
  resource_group_name = data.azurerm_resource_group.target.name
  vnet_name           = var.vnet_name
  vnet_address_space  = var.vnet_address_space
  subnet_name         = var.subnet_name
  subnet_address_prefix = var.subnet_address_prefix
  tags                = var.tags
}

module "os_image" {
  source = "./modules/os_image"

  windows_server_2025_image_id = var.ws2025_image_id
}

module "vm_upgrade" {
  source = "./modules/vm_upgrade"

  admin_username      = var.admin_username
  admin_password      = data.azurerm_key_vault_secret.local_admin_password.value
  location            = data.azurerm_resource_group.target.location
  name                = var.vm_name
  resource_group_name = data.azurerm_resource_group.target.name
  subnet_id           = module.network.subnet_id
  virtual_machine_size = var.vm_size
  source_image_id     = module.os_image.windows_server_2025_image_id
  tags                = var.tags
}
