resource "azurerm_virtual_network" "spoke" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
  tags                = var.tags
}

resource "azurerm_subnet" "spoke" {
  for_each             = { for s in var.subnets : s.name => s }
  name                 = each.value.name
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.spoke.name
  address_prefixes     = [each.value.prefix]
}

resource "azurerm_route_table" "egress" {
  name                = "${var.name}-egress"
  location            = var.location
  resource_group_name = var.resource_group_name
  disable_bgp_route_propagation = false
  tags                = var.tags

  route {
    name                   = "default-egress"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = var.firewall_private_ip
  }
}

resource "azurerm_subnet_route_table_association" "egress" {
  for_each       = azurerm_subnet.spoke
  subnet_id      = each.value.id
  route_table_id = azurerm_route_table.egress.id
}

resource "azurerm_virtual_network_peering" "to_hub" {
  name                      = "${var.name}-to-hub"
  resource_group_name       = var.resource_group_name
  virtual_network_name      = azurerm_virtual_network.spoke.name
  remote_virtual_network_id = var.hub_vnet_id
  allow_forwarded_traffic   = true
  allow_gateway_transit     = true
  use_remote_gateways       = false
}

resource "azurerm_virtual_network_peering" "from_hub" {
  name                      = "hub-to-${var.name}"
  resource_group_name       = split("/", var.hub_vnet_id)[4]
  virtual_network_name      = split("/", var.hub_vnet_id)[8]
  remote_virtual_network_id = azurerm_virtual_network.spoke.id
  allow_forwarded_traffic   = true
  allow_gateway_transit     = false
  use_remote_gateways       = false
}
