resource "azurerm_virtual_network" "hub" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
  tags                = var.tags
}

resource "azurerm_subnet" "firewall" {
  name                 = "AzureFirewallSubnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [var.firewall_subnet_prefix]
}

resource "azurerm_public_ip" "firewall" {
  name                = "${var.name}-afw-pip"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_firewall_policy" "hub" {
  name                = "${var.name}-afw-policy"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_firewall_policy_rule_collection_group" "outbound" {
  name               = "outbound-security"
  firewall_policy_id = azurerm_firewall_policy.hub.id
  priority           = 100

  application_rule_collection {
    name     = "windows-update"
    priority = 100
    action   = "Allow"

    rule {
      name             = "windows-update"
      source_addresses = ["10.0.0.0/8"]
      target_fqdns     = ["windowsupdate.microsoft.com", "download.microsoft.com"]
      protocols {
        type = "Https"
        port = 443
      }
    }
  }

  network_rule_collection {
    name     = "monitoring"
    priority = 200
    action   = "Allow"

    rule {
      name                  = "azure-monitor"
      protocols             = ["TCP"]
      source_addresses      = ["10.0.0.0/8"]
      destination_addresses = ["AzureMonitor"]
      destination_ports     = ["443"]
    }
  }
}

resource "azurerm_firewall" "hub" {
  name                = "${var.name}-afw"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = "AZFW_VNet"
  sku_tier            = "Standard"
  firewall_policy_id  = azurerm_firewall_policy.hub.id

  ip_configuration {
    name                 = "configuration"
    subnet_id            = azurerm_subnet.firewall.id
    public_ip_address_id = azurerm_public_ip.firewall.id
  }

  tags = var.tags
}
