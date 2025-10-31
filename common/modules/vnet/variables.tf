variable "name" {
  description = "Name of the spoke virtual network"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group containing the VNet"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "address_space" {
  description = "Address space for the VNet"
  type        = list(string)
}

variable "subnets" {
  description = "List of subnet definitions"
  type = list(object({
    name   = string
    prefix = string
  }))
}

variable "firewall_private_ip" {
  description = "Private IP address of the Azure Firewall in the hub"
  type        = string
}

variable "hub_vnet_id" {
  description = "Resource ID of the hub VNet for peering"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
