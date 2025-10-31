# Security Architecture Overview

This document summarizes the security architecture for aligning CPS controls with Azure governance, enforcing Windows Server 2025 baselines in Azure AD DS, and orchestrating approvals through the ASUK security Change Advisory Board (CAB).

## 1. Architecture Principles

- **Subscription-Centric Governance:** Apply CPS initiatives at the subscription scope to enable consistent compliance scoring across landing zones.
- **Automated Baseline Enforcement:** Use Azure Automation DSC to re-apply Microsoft security baselines after platform upgrades.
- **Assurance via CAB:** All high-impact security deployments must pass through the ASUK security CAB before execution in production.

## 2. Components

| Component | Description |
|-----------|-------------|
| Azure Policy Management Group | Hosts CPS initiative definitions and handles central version control. |
| Subscription Assignments | Enforce CPS controls using policy assignments with managed identities. |
| Azure AD DS Managed Domain | Receives Windows Server 2025 baseline GPO imports. |
| Azure Automation Account | Executes DSC compilations and maintains configuration state. |
| Log Analytics & Sentinel | Aggregates compliance data and security signals. |
| ASUK Security CAB | Manual validation gate for change control, integrated via pipeline approval. |

## 3. Data Flow

1. Platform security pipeline runs according to `pipelines/security-baseline.yml`.
2. Policy stage assigns CPS initiatives to subscriptions and triggers remediation.
3. Baseline stage publishes the DSC configuration and awaits CAB approval.
4. Upon approval, DSC jobs run on hybrid workers to re-apply the Windows Server 2025 baseline.
5. Compliance data is exported to the CPS dashboard and SIEM.

## 4. Security Controls Traceability

- `docs/cps-azure-policy-mapping.md` catalogs the mapping between CPS controls and Azure Policy initiatives.
- `dsc/Apply-Windows2025Baseline.ps1` describes the configuration artifacts that ensure baseline consistency.
- Pipeline manual validation enforces CAB oversight for each deployment run.

## 5. Operational Processes

- Maintain Git-based versioning of initiatives, DSC scripts, and configuration data.
- Use environment-specific parameter files for policy assignments (stored securely in Key Vault).
- Record CAB outcomes and remediation steps in the security register for audit.

## 6. Future Enhancements

- Integrate Just-In-Time (JIT) VM access enforcement into the CPS initiatives.
- Extend DSC coverage to include member servers joined to Azure AD DS.
- Automate exception request workflows via ServiceNow integration with the pipeline approval gate.
