variable "subscription_id" {
  type        = string
  description = "Azure subscription ID for resource deployment."
}

variable "tenant_id" {
  type        = string
  description = "Azure Active Directory tenant ID."
}

variable "location" {
  type        = string
  description = "Azure region for all resources."
  default     = "eastus"
}

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to create."
}

variable "vm_name" {
  type        = string
  description = "Windows virtual machine name."
}

variable "admin_username" {
  type        = string
  description = "Administrator username for the Windows VM."
}

variable "admin_password" {
  type        = string
  description = "Administrator password for the Windows VM."
  sensitive   = true
}

variable "virtual_network_cidr" {
  type        = string
  description = "CIDR block for the virtual network."
  default     = "10.10.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR block for the subnet."
  default     = "10.10.1.0/24"
}

variable "ws2025_iso_source_uri" {
  type        = string
  description = "URI to the WS2025 ISO VHD/managed disk source blob."
}

variable "iso_disk_size_gb" {
  type        = number
  description = "Size in GB for the ISO managed disk."
  default     = 15
}

variable "upgrade_trigger_version" {
  type        = string
  description = "Version marker that forces the upgrade null_resource to re-run when changed."
  default     = "2025.0"
}

variable "log_analytics_workspace_name" {
  type        = string
  description = "Name for the Log Analytics workspace."
  default     = "ws2025-upgrade-law"
}

variable "log_analytics_sku" {
  type        = string
  description = "SKU for the Log Analytics workspace."
  default     = "PerGB2018"
}

variable "action_group_short_name" {
  type        = string
  description = "Short name for the action group."
  default     = "ws2025"
}

variable "action_group_email" {
  type        = string
  description = "Email address to receive failure alerts."
}

variable "ansible_playbook_path" {
  type        = string
  description = "Path to the Ansible playbook to reapply configuration after upgrade."
  default     = "C:\\Ansible\\playbooks\\post-upgrade.yml"
}

variable "dsc_configuration_path" {
  type        = string
  description = "Path to the DSC configuration folder on the VM."
  default     = "C:\\DSC\\Configurations"
}
