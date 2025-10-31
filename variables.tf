variable "resource_group_name" {
  description = "Name of the target resource group hosting the deployment."
  type        = string
}

variable "key_vault_name" {
  description = "Name of the Azure Key Vault containing deployment secrets."
  type        = string
}

variable "key_vault_resource_group" {
  description = "Resource group containing the Key Vault."
  type        = string
}

variable "admin_password_secret_name" {
  description = "Secret name storing the local administrator password."
  type        = string
}

variable "admin_username" {
  description = "Local administrator username for the virtual machine."
  type        = string
  default     = "localadmin"
}

variable "vm_name" {
  description = "Name of the Windows virtual machine."
  type        = string
}

variable "vm_size" {
  description = "Size of the Windows virtual machine."
  type        = string
  default     = "Standard_D4s_v5"
}

variable "vnet_name" {
  description = "Name of the virtual network."
  type        = string
  default     = "core-vnet"
}

variable "vnet_address_space" {
  description = "Address spaces assigned to the virtual network."
  type        = list(string)
  default     = ["10.10.0.0/16"]
}

variable "subnet_name" {
  description = "Name of the subnet hosting the virtual machine."
  type        = string
  default     = "vm-subnet"
}

variable "subnet_address_prefix" {
  description = "CIDR prefix for the subnet."
  type        = string
  default     = "10.10.1.0/24"
}

variable "ws2025_image_id" {
  description = "Compute Gallery image ID for Windows Server 2025."
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
