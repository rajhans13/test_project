output "virtual_machine_id" {
  description = "Identifier of the Windows virtual machine deployed by the vm_upgrade module."
  value       = module.vm_upgrade.virtual_machine_id
}

output "network_subnet_id" {
  description = "Identifier of the subnet hosting the Windows virtual machine."
  value       = module.network.subnet_id
}
