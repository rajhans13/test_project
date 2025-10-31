# CPS Control to Azure Policy Mapping

This document maps the key Cyber Protection System (CPS) controls to Azure Policy set (initiative) assignments that will be applied at the subscription scope. Each initiative bundles the required policy definitions and delivers consistent compliance reporting across landing zones.

## Subscription-Level Initiatives

| CPS Control | Objective | Azure Policy Set (Initiative) | Included Policies | Assignment Scope | Notes |
|-------------|-----------|-------------------------------|-------------------|------------------|-------|
| CPS-01: Encrypt Compute at Rest | Ensure virtual machines use encrypted OS and data disks | `CPS-Encrypt-Compute` | - `Audit VMs without encryption`<br>- `Deploy Azure Disk Encryption for Windows/Linux VMs` | All production subscriptions | Assignment configured with managed identity having Key Vault access; remediation tasks automatically enabled. |
| CPS-02: Protect Platform Updates | Enforce baseline patching and update management | `CPS-Patch-Compliance` | - `Configure periodic updates for Windows VMs`<br>- `Audit missing system updates` | Subscriptions hosting Windows Server workloads | Linked to Azure Automation Update Management workspace. |
| CPS-03: Safeguard Network Boundaries | Restrict exposure via NSGs and Azure Firewall | `CPS-Network-Hardening` | - `Audit NSGs that allow inbound internet traffic`<br>- `Require secure transport on private endpoints`<br>- `Deploy Azure Firewall for hub virtual networks` | Connectivity subscriptions | Policy parameters enforce approved service tags only. |
| CPS-04: Secure Identity Plane | Harden privileged access and identity logging | `CPS-Identity-Security` | - `Require MFA for owners`<br>- `Deploy Azure AD sign-in logging to Log Analytics` | Management subscription | Initiative references built-in Defender for Cloud connector for centralized monitoring. |
| CPS-05: Monitor Data Protection | Ensure storage services are encrypted and monitored | `CPS-Data-Protection` | - `Audit storage accounts without secure transfer`<br>- `Enforce double encryption on Azure SQL`<br>- `Deploy Azure Monitor diagnostic settings for Storage` | All data platforms subscriptions | Diagnostic settings stream to the central Sentinel workspace. |

## Assignment Workflow

1. Create or import the initiative definitions in a central management group.
2. Parameterize initiatives for environment-specific settings (e.g., Log Analytics workspace IDs, allowed locations).
3. Use Azure Policy assignments at the subscription scope with system-assigned managed identities.
4. Enable remediation tasks for deploy-if-not-exists and modify policies to ensure drift is corrected automatically.
5. Capture compliance results in the CPS compliance dashboard (Power BI) via the Azure Policy compliance data connector.

## Automation Snippet

```azurecli
# Assign the CPS-Encrypt-Compute initiative to a subscription
az policy assignment create \
  --name cps-encrypt-compute \
  --display-name "CPS-Encrypt-Compute" \
  --scope "/subscriptions/<subscription-id>" \
  --policy-set-definition cps-encrypt-compute \
  --identity-type SystemAssigned \
  --location uksouth \
  --params @params/encrypt-compute.json
```

The automation is invoked by the platform compliance pipeline (see `pipelines/security-baseline.yml`) to ensure consistency across environments.
