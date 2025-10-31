# Technical Approach for SOE 2025 Azure Migration

## 1 Planning & Modernization

### 1.1 Discovery and Assessment
- **Inventory & dependency mapping:** Use ASUK’s CMDB and Azure Migrate discovery tools to build a complete inventory of Windows Server 2016 hosts. Collect quantitative data (SKU, CPU/RAM, applications installed) and validate with application owners. Identify application dependencies and note any special servers (e.g. jump hosts, SCCM, SonarQube).
- **Qualitative analysis:** For each application, record its tech stack, criticality, complexity and testing requirements. This helps prioritize applications for waves.
- **Application prioritization:** Together with ASUK, rank applications by strategic importance and risk. Select 3–5 non-business-critical workloads for a pilot.
- **Stakeholder & governance alignment:** Identify ASUK stakeholders (architecture, security, change management). Define maintenance windows, escalation paths and point-of-contact lists.

### 1.2 Architecture and Wave Planning
- **Landing zone design:** Create separate Azure subscriptions and resource groups for Dev, Test/UAT, Prod and DR. Use hub-and-spoke networking or VNET peering with subnets per tier, and apply NSGs and Azure Firewall.
- **Golden image creation:** Build a hardened Windows Server 2025 image in Azure Compute Gallery, including baseline agents (Defender for Cloud, monitoring, backup) and GPO settings.
- **Repository & package structure:** Follow the recommended repo layout: directories for environment config (`/env`), shared utilities (`/common`), instrument definitions (`/im`), datasets, ETL jobs and providers. Use camel-cased provider names and maintain a package descriptor with fields like group, name, version, description, components and requires.
- **Branching strategy:** Adopt Gitflow: develop features on `feature/<ticket>` branches, merge into `dev`, promote to `main` for UAT, and then to `prod`. Always include ticket numbers and squash commits.
- **CI/CD pipeline design:** Implement Azure DevOps multi-stage YAML pipelines. Include build (lint, tests), plan (terraform plan), approval gates and apply stages. Add manual approvals between Dev, Test and Prod. Integrate style guides and code-quality scans.

### 1.3 Modernization of Infrastructure-as-Code
- **Terraform modules:** Develop reusable modules for VMs, networks and OS upgrades. Update them to reference Windows Server 2025 images and parameterize environment-specific details.
- **Parameterization:** Store environment-specific values in variables; keep secrets in Azure Key Vault; avoid hard-coding environment names.
- **Quality gates:** Run `terraform fmt`, `terraform validate` and `tflint` in the pipeline. Generate module documentation automatically. Enforce PR checklist items (directory structure, manifest, scopes, comments and tests).

### 1.4 Security & Compliance Planning
- **Compliance alignment:** Map controls to APRA CPS 231/234. Enforce encryption at rest, RBAC and MFA. Document security architecture for ASUK’s review.
- **Baseline policies:** Apply Microsoft’s Windows Server 2025 security baseline and enforce via Azure Policy. Ensure GPOs reapply post-upgrade.
- **Security review:** Present detailed designs and pipeline code for ASUK’s security approval.

## 2 Pilot Migration

### 2.1 Pilot Pipeline Development
- **Upgrade pipeline:** Build an Azure DevOps pipeline that snapshots existing OS and data disks via Azure Backup, creates and attaches a Windows Server 2025 ISO disk from Azure Marketplace to each VM, runs an unattended upgrade using a PowerShell script executed by Terraform’s remote-exec provisioner, detaches the ISO disk, reboots the VM, and reapplies baseline configuration.
- **Configuration management:** Use PowerShell DSC or Ansible to enforce GPO, join domain, and install agents after upgrade.
- **Logging:** Capture upgrade logs in Azure Monitor; configure alerts for failures or extended duration.

### 2.2 Pilot Testing & Validation
- **Functional testing:** Verify application start-up, login policies, and key workflows.
- **Policy and security checks:** Confirm GPO compliance, Defender for Cloud recommendations, and overall security baseline.
- **Performance comparison:** Compare CPU, memory and disk metrics against pre-migration baselines; adjust VM sizes or disk types if needed.
- **Rollback verification:** Test the rollback plan by intentionally failing an upgrade and restoring from snapshots.

### 2.3 Pilot Review and Improvement
- Conduct a retrospective with ASUK teams. Capture lessons learned; update Terraform modules, scripts and runbooks; obtain formal sign-off before full rollout.

## 3 Full Rollout

### 3.1 Wave Planning & Scheduling
- **Move group definition:** Use dependency mappings to group tightly coupled applications. Plan waves from least to most critical.
- **Communication:** Notify users and owners about maintenance windows and expected downtimes; obtain change-control approvals.
- **Capacity readiness:** Ensure Azure quotas and network resources are provisioned ahead of each wave.

### 3.2 Wave Execution
- **Pre-migration:** Freeze changes, back up VMs, update pipeline variables for target environment.
- **Migration:** Execute the upgrade pipeline across all VMs in the wave; monitor for failures.
- **Post-migration validation:** Run automated smoke tests and configuration checks; only enable production traffic once tests pass.
- **Wave sign-off:** Record results, update documentation and obtain owner approval before starting the next wave.

### 3.3 Version Control & Release Management
- Maintain release branches tied to OS versions and tag each successful wave (e.g., `v2025.1.0`). Use squash merges and ticket numbers. Store Terraform state remotely to ensure consistency.

### 3.4 Automation & Observability
- **Pipeline templates:** Parameterize OS image IDs and environment variables; reuse templates across repositories.
- **Monitoring:** Deploy Azure Monitor dashboards to track upgrade status, VM health, and performance; set alerts for anomalies.
- **Reporting:** Generate automated reports summarizing upgraded servers, results (success/failure/rollback), and lessons learned.

## 4 Stabilization & Hypercare

### 4.1 Hypercare Support
- Allocate a dedicated support team for at least two weeks post-wave. Use runbooks for common issues; integrate alerts with ASUK’s ITSM tool. Monitor performance and cost; right-size or auto-scale as needed.

### 4.2 Knowledge Transfer & Handover
- Produce detailed runbooks covering upgrade pipeline, rollback procedures, and troubleshooting. Conduct training sessions for ASUK operations and DevOps teams.

### 4.3 Security & Compliance Verification
- Perform final vulnerability scans (Defender for Cloud). Verify encryption, patching and privileged-access configurations. Provide compliance evidence to ASUK.

## 5 Cleanup & Project Closure

### 5.1 Decommissioning
- Retire old Windows Server 2016 VMs after a grace period. Remove unused snapshots/disks and update the CMDB. Terminate any support contracts tied to old infrastructure.

### 5.2 Documentation & Retrospective
- Compile a final report summarising the migration: number of servers upgraded, total downtime, issues and resolutions. Update architecture diagrams and IaC documentation. Conduct a project retrospective to capture improvements for future migrations.

## Development Standards & Best Practices
- **Coding conventions:** Follow PEP 8 for Python and Simon Holywell’s SQL style guide. Use uppercase SQL keywords and snake_case columns. Include headers in scripts (Title, Description, Author, version) and adopt Semantic Versioning.
- **Repo organisation:** Use the recommended repo structure with separate directories for configuration, common code, instruments, datasets and ETL jobs.
- **Pull-request checklist:** During code reviews, verify directory structure, manifest inclusion, scopes, comments and tests. Reviewers resolve comments inline and squash merges include ticket numbers.
- **Branch naming & semantic versioning:** Use `feature/<ticket>-description`, `hotfix/<ticket>` patterns; maintain version numbers in modules and packages.
- **CI/CD strategy:** Employ multi-stage pipelines with manual approvals and integrate style checks and tests. Maintain distinct environments (Dev, SIT, UAT, Prod, DR) with clear networking and security boundaries.
