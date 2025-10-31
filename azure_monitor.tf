resource "azurerm_monitor_action_group" "itsm_webhook" {
  name                = "hypercare-itsm-ag"
  resource_group_name = var.azure_resource_group_name
  short_name          = "ITSMAG"

  webhook_receiver {
    name                    = "itsm-webhook"
    service_uri             = var.itsm_webhook_url
    use_common_alert_schema = true
    custom_headers          = var.itsm_webhook_headers
  }
}

resource "azurerm_monitor_metric_alert" "cpu_anomaly" {
  name                = "hypercare-cpu-anomaly"
  resource_group_name = var.azure_resource_group_name
  scopes              = [var.azure_target_resource_id]
  description         = "Alert when CPU usage stays above the defined threshold to auto-create ITSM incidents."
  severity            = 2
  frequency           = format("PT%vM", var.alert_frequency_in_minutes)
  window_size         = format("PT%vM", var.alert_frequency_in_minutes)
  auto_mitigate       = true

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = var.alert_cpu_threshold
  }

  action {
    action_group_id = azurerm_monitor_action_group.itsm_webhook.id
  }

  tags = {
    workload = "hypercare"
    purpose  = "itsm-autocreation"
  }
}

output "pagerduty_integration_key" {
  description = "Routing key for Azure Monitor or automation workflows to send PagerDuty incidents."
  value       = pagerduty_service_integration.azure_events.integration_key
  sensitive   = true
}
