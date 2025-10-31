terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
    pagerduty = {
      source  = "pagerduty/pagerduty"
      version = "~> 2.14"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
  client_id       = var.azure_client_id
  client_secret   = var.azure_client_secret
}

provider "pagerduty" {
  token = var.pagerduty_token
}
