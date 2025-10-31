resource "pagerduty_schedule" "primary_oncall" {
  name      = "Hypercare Primary On-Call"
  time_zone = var.pagerduty_time_zone

  layer {
    name                         = "Primary"
    rotation_virtual_start       = "2024-01-01T00:00:00Z"
    rotation_turn_length_seconds = 86400
    users                        = var.pagerduty_users
  }
}

resource "pagerduty_escalation_policy" "hypercare" {
  name        = "Hypercare Escalation Policy"
  description = "Escalation path for hypercare production incidents"

  rule {
    escalation_delay_in_minutes = 15
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.primary_oncall.id
    }
  }
}

resource "pagerduty_service" "hypercare" {
  name                    = var.pagerduty_service_name
  escalation_policy       = pagerduty_escalation_policy.hypercare.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600
}

resource "pagerduty_service_integration" "azure_events" {
  name    = "Azure Monitor"
  type    = "events_api_v2_inbound_integration"
  service = pagerduty_service.hypercare.id
}
