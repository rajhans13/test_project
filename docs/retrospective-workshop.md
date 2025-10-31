# Platform Reliability Retrospective – Q1 2025

## Workshop Overview
- **Facilitator:** Platform Operations (automated notes by AI assistant)
- **Date:** 2025-02-18
- **Scope:** Review of January production scaling waves and associated incidents across Terraform-based infrastructure, Azure Automation runbooks, and Desired State Configuration (DSC) artifacts.

## Key Themes
1. **Observability gaps during scaling waves** – lack of consolidated dashboards for Terraform and Azure Automation executions.
2. **Configuration drift** – DSC node configurations lagging behind Terraform module updates.
3. **Change governance friction** – CAB approvals captured inconsistently, delaying ASUK sign-off.

## Action Items for Azure DevOps Wiki
| ID | Title | Owner | Target Sprint | Notes |
| --- | --- | --- | --- | --- |
| AI-001 | Publish consolidated “Scaling Wave Observability” dashboard guidance | FinOps Team | Sprint 2025.04 | Embed Grafana + Azure Monitor queries and link automation runbook health checks. |
| AI-002 | Automate DSC compliance scans in nightly pipeline | Config Mgmt Team | Sprint 2025.04 | Extend `ApplyWebConfig.ps1` to emit compliance status artifacts. |
| AI-003 | Update Terraform module templates with versioned tagging contract | IaC Guild | Sprint 2025.03 | Align module tagging with `deployment_version` variable introduced in this iteration. |
| AI-004 | Standardize CAB note-taking template in Wiki | Release Mgmt | Sprint 2025.03 | Ensure ASUK sign-off is recorded before each scaling wave. |

## Next Steps
- Copy the action item table into the Azure DevOps Wiki under **Platform Operations ➜ Continuous Improvement ➜ 2025-Q1 Retrospective**.
- Assign owners via Azure Boards and link work items to the Wiki page for traceability.
- Schedule follow-up retrospective checkpoint during Sprint 2025.05 to validate completion.
