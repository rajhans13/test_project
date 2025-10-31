output "virtual_network_id" {
  value       = azurerm_virtual_network.hub.id
  description = "Resource ID of the hub VNet"
}

output "firewall_private_ip" {
  value       = azurerm_firewall.hub.ip_configuration[0].private_ip_address
  description = "Private IP address of the Azure Firewall"
}

output "firewall_policy_id" {
  value       = azurerm_firewall_policy.hub.id
  description = "Resource ID of the Azure Firewall policy"
}
