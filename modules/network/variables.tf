variable "location" {
  description = "Azure region for the networking resources."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name for the networking resources."
  type        = string
}

variable "vnet_name" {
  description = "Name of the virtual network to create."
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for the virtual network."
  type        = list(string)
}

variable "subnet_name" {
  description = "Name of the subnet to create."
  type        = string
}

variable "subnet_address_prefix" {
  description = "CIDR prefix of the subnet."
  type        = string
}

variable "tags" {
  description = "Tags to apply to the networking resources."
  type        = map(string)
  default     = {}
}
