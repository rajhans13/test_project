# Windows Server 2025 Security Baseline Deployment (Azure AD DS)

This runbook describes the approach for importing the Microsoft Windows Server 2025 security baseline Group Policy Objects (GPOs) into Azure Active Directory Domain Services (Azure AD DS) and enforcing the baseline with Desired State Configuration (DSC).

## Import Process

1. Download the official Microsoft Security Compliance Toolkit release for Windows Server 2025.
2. Extract the baseline GPO backups and copy them to the Azure AD DS management VM (joined to the managed domain).
3. Use the Azure AD DS Group Policy Management Console to create dedicated baseline GPOs (e.g., `WS2025-Computer-Baseline`, `WS2025-User-Baseline`).
4. Import the backed-up GPO settings via **Group Policy Management** > **Managed Domain** > **Group Policy Objects** > **Import Settings**.
5. Link the imported GPOs to the appropriate organizational units (OU) for tiered workloads.

## DSC Enforcement Strategy

- `dsc/Apply-Windows2025Baseline.ps1` ensures that after Azure AD DS domain controllers are upgraded or reimaged, the Windows Server 2025 baseline is re-applied.
- The script is executed by an Azure Automation account hybrid worker, triggered by the `Enforce-Windows2025Baseline` stage in the pipeline defined in `pipelines/security-baseline.yml`.
- Configuration data files (not in repo) capture OU bindings, baseline versions, and override exceptions for application compatibility.

## Validation

1. Run `Get-GPOReport` to verify the imported GPOs match the Microsoft baseline.
2. Execute the DSC configuration in `Test` mode before full application to capture drift.
3. Integrate Defender for Cloud regulatory compliance dashboard to monitor adherence.

## Operational Considerations

- Maintain version tags for the imported baselines to simplify rollback (e.g., `WS2025-baseline-v1`).
- Document exceptions approved through the security CAB in the compliance register.
- Schedule quarterly re-validation to align with Microsoft baseline updates.
