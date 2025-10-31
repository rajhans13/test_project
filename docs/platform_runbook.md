# Platform Runbook

## Overview
This runbook documents the end-to-end CI/CD pipeline for the ASUK application stack, including deployment flow, rollback procedures, and troubleshooting guidance. It consolidates the artefacts that must be published to Confluence. Update the authoritative copy in Confluence after each release, and link back to this repository for version control history.

## Pipeline Flow
1. **Source Control (GitHub)**
   - Developers open feature branches, trigger pull-request checks, and obtain reviews.
   - Required checks: unit tests, Terraform validation (`terraform fmt -check`, `terraform validate`), security scan (`tfsec`), and integration smoke tests.
2. **Continuous Integration (GitHub Actions)**
   - Workflow `ci.yml` runs on pull requests.
   - Stages: checkout → dependency caching → lint/test → Terraform plan (using `-out` artifact) → Docker image build and push to ECR with commit SHA tag.
3. **Artifact Promotion**
   - On merge to `main`, workflow `release.yml` executes.
   - Steps: retrieve stored Terraform plan → apply to staging → run post-deploy tests → upon success, create release tag and push immutable Docker image to production repository.
4. **Infrastructure Deployment (Terraform)**
   - Workspaces: `dev`, `staging`, `prod`.
   - Backend: S3 state bucket `asuk-terraform-state`, DynamoDB table for state locking.
   - Apply order: networking (`main.tf.rtf`), security groups (`sg.tf.rtf`), compute deployment (`create-deployment.rtf`), outputs (`output.tf.rtf`).
5. **Application Release (ArgoCD)**
   - ArgoCD monitors Helm chart in `deploy/helm` branch.
   - Promotion triggered by updating image tag via GitHub Action `promote-prod`.

## Rollback Procedures
### Application Rollback
1. Identify failing release version and last known good image tag.
2. Update ArgoCD application values to point to previous tag using the `promote-prod` workflow input `rollback_version`.
3. Approve the manual gate in ArgoCD; monitor rollout until healthy.
4. Post-rollout verification: run synthetic transaction and check CloudWatch alarms.

### Infrastructure Rollback
1. For Terraform failures during apply:
   - Review plan/apply logs in GitHub Actions artifacts.
   - Run `terraform state list` to confirm partial resources; if needed, use `terraform state rm` for failed resources before re-apply.
2. For misconfiguration detected post-apply:
   - Revert the offending commit in Git, merge to `main`.
   - Execute `terraform apply` via `release.yml` to restore previous desired state.
3. Emergency rollback:
   - Use S3 state versioning to restore previous `terraform.tfstate` version.
   - Lock state, download prior version, replace current state, and run `terraform refresh` followed by targeted apply.

## Troubleshooting Guide
| Symptom | Diagnostic Steps | Resolution |
| --- | --- | --- |
| CI pipeline fails at Terraform Plan | Check `terraform fmt` output for formatting errors; run `terraform fmt` locally. Ensure AWS credentials are valid. | Correct syntax, re-run pipeline. |
| Apply blocked by state lock | Inspect DynamoDB lock entry (`asuk-terraform-lock`). Remove stale lock via AWS CLI once no operations are running. | Delete lock item and re-run apply. |
| Deployment healthy but app unreachable | Validate security group ingress in `sg.tf.rtf`; verify ALB listener status. | Update SG rules, run `terraform apply`. |
| Elevated latency post-release | Compare metrics in CloudWatch dashboards, review pods via `kubectl describe`. | Scale up HPA thresholds or roll back application version. |
| ArgoCD sync errors | Check ArgoCD UI sync diff; ensure Helm chart values updated and secrets present. | Correct values, re-sync. |

## Confluence Publishing Checklist
- [ ] Copy `Pipeline Flow`, `Rollback Procedures`, and `Troubleshooting Guide` sections to Confluence page `ASUK Ops > Runbooks > Platform`.
- [ ] Update Confluence page version history with release identifier.
- [ ] Attach GitHub release notes and Terraform plan artifact links.
- [ ] Notify Ops & DevOps in #asuk-release channel.

## Contacts
- **Primary On-call:** ASUK Ops Rotation (PagerDuty schedule `asuk-ops`).
- **Escalation:** DevOps Lead (devops-lead@asuk.example.com).
- **Product Owner:** asuk-product@example.com.

