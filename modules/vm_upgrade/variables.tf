variable "name" {
  description = "Name of the Windows virtual machine."
  type        = string
}

variable "location" {
  description = "Azure region for the virtual machine."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name for the virtual machine."
  type        = string
}

variable "virtual_machine_size" {
  description = "Azure VM size."
  type        = string
}

variable "admin_username" {
  description = "Local administrator username."
  type        = string
}

variable "admin_password" {
  description = "Local administrator password retrieved from Key Vault."
  type        = string
  sensitive   = true
}

variable "subnet_id" {
  description = "Subnet identifier for the virtual machine's primary NIC."
  type        = string
}

variable "source_image_id" {
  description = "Compute Gallery image identifier for the VM."
  type        = string
}

variable "tags" {
  description = "Tags to apply to the VM resources."
  type        = map(string)
  default     = {}
}
