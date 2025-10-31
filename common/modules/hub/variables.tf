variable "name" {
  description = "Name of the hub virtual network"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group that hosts the hub resources"
  type        = string
}

variable "location" {
  description = "Azure region for the hub"
  type        = string
}

variable "address_space" {
  description = "Address space for the hub VNet"
  type        = list(string)
}

variable "firewall_subnet_prefix" {
  description = "CIDR block for the Azure Firewall subnet"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
