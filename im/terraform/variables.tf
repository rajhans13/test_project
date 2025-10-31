variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
}

variable "management_subscription_id" {
  description = "Subscription used to deploy shared infrastructure"
  type        = string
}

variable "root_management_group_id" {
  description = "Root management group for policy assignments"
  type        = string
}

variable "policy_definition_ids" {
  description = "Map of policy definition IDs to assign at the management group level"
  type        = map(string)
}

variable "location" {
  description = "Default Azure region for networking resources"
  type        = string
  default     = "eastus2"
}

variable "resource_group_name" {
  description = "Resource group hosting shared network components"
  type        = string
}

variable "tags" {
  description = "Global resource tags"
  type        = map(string)
  default     = {}
}
