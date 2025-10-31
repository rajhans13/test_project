output "vm_public_ip" {
  description = "Public IP address of the Windows VM."
  value       = azurerm_public_ip.this.ip_address
}

output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace used for diagnostics."
  value       = azurerm_log_analytics_workspace.this.id
}

output "recovery_services_vault_id" {
  description = "Resource ID of the Recovery Services vault protecting the VM."
  value       = azurerm_recovery_services_vault.this.id
}

output "backup_alert_action_group_id" {
  description = "Resource ID of the action group that receives backup failure alerts."
  value       = azurerm_monitor_action_group.backup_failures.id
}
