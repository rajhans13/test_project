output "network_interface_id" {
  description = "Identifier of the network interface created for the VM."
  value       = azurerm_network_interface.this.id
}

output "virtual_machine_id" {
  description = "Identifier of the Azure Windows virtual machine."
  value       = azurerm_windows_virtual_machine.this.id
}
