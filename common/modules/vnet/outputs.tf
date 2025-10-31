output "virtual_network_id" {
  value       = azurerm_virtual_network.spoke.id
  description = "Resource ID of the spoke VNet"
}

output "subnet_ids" {
  value       = { for k, subnet in azurerm_subnet.spoke : k => subnet.id }
  description = "Map of subnet resource IDs"
}
