# Cost and Performance Monitoring Playbook

## Overview
The Cost Management playbook defines how the team monitors spend and performance signals for the hypercare workload. Dashboards combine Azure Cost Management data with performance metrics to trigger right-sizing actions when anomalies are detected.

## Dashboards
- **Hypercare Cost Overview** – Tracks daily burn rate, forecast vs. budget, and subscription-level anomalies.
- **Compute Efficiency** – Correlates VM cost with CPU, memory, and disk queue length statistics pulled from Log Analytics.
- **Storage Utilization** – Highlights premium disks with low throughput to target for resizing.

Dashboards are created in Azure Cost Management + Billing and pinned to the Hypercare operations shared dashboard workspace. Owners must validate refresh scheduling weekly.

## Alerting Workflow
1. Configure Cost Management anomaly detection for the hypercare resource group with a 20% threshold.
2. Route anomaly alerts to the PagerDuty Hypercare service (routing key exposed via Terraform output `pagerduty_integration_key`).
3. Create Azure Monitor budget alerts for monthly spend limits and subscribe the ITSM webhook action group for ticketing.

## Response Actions
- **Cost Spike Detected**
  1. Validate anomaly scope in the Cost Overview dashboard.
  2. Cross-check resource metrics in Compute Efficiency to confirm performance impact.
  3. If cost increase is unjustified, initiate right-sizing or stop non-essential VMs.
- **Performance Degradation with Cost Increase**
  1. Review VM SKU utilization.
  2. If CPU > 80% for more than 1 hour, scale up to next SKU and document in ITSM ticket.
  3. After remediation, annotate dashboard with resolution summary.

## Governance
- Review dashboards during weekly hypercare standup.
- Archive historical cost exports to the `finops` storage account for quarterly analysis.
- Update Terraform variables when adding new monitored resources so anomaly rules stay accurate.
