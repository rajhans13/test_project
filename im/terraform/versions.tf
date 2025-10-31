terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.12"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.management_subscription_id
}

provider "azapi" {}
