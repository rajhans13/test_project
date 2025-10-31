variable "azure_subscription_id" {
  description = "Azure subscription identifier used for monitoring resources."
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure AD tenant identifier for service principal authentication."
  type        = string
}

variable "azure_client_id" {
  description = "Service principal application ID with permissions to manage Monitor resources."
  type        = string
}

variable "azure_client_secret" {
  description = "Service principal secret for Azure authentication."
  type        = string
  sensitive   = true
}

variable "azure_resource_group_name" {
  description = "Resource group that contains the target workload to monitor."
  type        = string
}

variable "azure_target_resource_id" {
  description = "Resource ID of the workload emitting the metric signal."
  type        = string
}

variable "itsm_webhook_url" {
  description = "Webhook endpoint provided by the ITSM system for incident creation."
  type        = string
  sensitive   = true
}

variable "itsm_webhook_headers" {
  description = "Optional custom headers to include when invoking the ITSM webhook."
  type        = map(string)
  default     = {}
}

variable "pagerduty_token" {
  description = "PagerDuty API token with rights to manage schedules and services."
  type        = string
  sensitive   = true
}

variable "pagerduty_time_zone" {
  description = "Time zone for the on-call rota."
  type        = string
  default     = "UTC"
}

variable "pagerduty_users" {
  description = "List of PagerDuty user IDs participating in the schedule."
  type        = list(string)
}

variable "pagerduty_service_name" {
  description = "Name of the PagerDuty service receiving alerts."
  type        = string
  default     = "Hypercare Service"
}

variable "alert_cpu_threshold" {
  description = "CPU percentage threshold that triggers the Azure Monitor alert."
  type        = number
  default     = 85
}

variable "alert_frequency_in_minutes" {
  description = "Frequency in minutes at which the metric alert evaluates the signal."
  type        = number
  default     = 5
}
