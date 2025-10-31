# Release Wave Process

This project delivers infrastructure changes in controlled "wave" releases. The following workflow standardises branching, state management, tagging, and secret rotation.

## 1. Create/maintain release branches

Use `scripts/release_wave.sh` to create or refresh release branches named `release/v2025.<wave>`.

```bash
./scripts/release_wave.sh start --wave 1 --base main --push
```

The script fast-forwards the release branch from the base branch (default `main`) and optionally pushes it to `origin`. The branch name suffix (`<wave>`) can be numeric or alphanumeric but must not contain `/`.

## 2. Complete a wave with a squash merge

After validating the release, squash merge back into the target branch (default `main`) with the ticket reference embedded in the commit message:

```bash
./scripts/release_wave.sh complete --wave 1 --ticket ABC-123 --outcome success --push
```

The command produces a commit message like `Wave 1 (success) [ABC-123]`, ensuring auditability for the associated work item. Push the commit and trigger the Azure DevOps pipeline to roll forward.

## 3. Terraform state in Azure Storage with automatic locking

Terraform now uses the Azure Storage backend (configured in `main.tf.rtf`). The Azure DevOps pipeline renders a `backend.hcl` file with backend settings and executes `terraform init` using the secret retrieved from Azure Key Vault. Azure Blob leases provide native state locking, protecting concurrent plans/applies.

Secrets are rotated by updating the `tfstatestoragekey` secret in Key Vault. Because the pipeline queries the secret at runtime, any rotated key is automatically consumed on the next run without code changes.

## 4. Automated tagging after successful waves

`azure-pipelines.yml` runs on `release/v2025.*` branches. After a successful wave (and optional `terraform apply`), the pipeline creates an annotated git tag using the `GitTag@1` task:

```
wave-<wave>-<outcome>
```

The annotation message includes the ticket ID supplied to the pipeline (for example via variable groups or run-time variables).

Set the following pipeline variables/secret references before running the release:

| Variable | Purpose |
| --- | --- |
| `ticketId` | Reference to the work item/ticket for squash merge and tag annotations. |
| `waveOutcome` | Outcome string such as `success`, `rollback`, or `hotfix`. |
| `runApply` | When set to `true`, `terraform apply` executes using the plan from the same run. |
| `stateAccessKeySecretName` | Name of the Key Vault secret (`tfstatestoragekey`) containing the Storage Account access key. |

Ensure the Azure service connection used by the pipeline has `Storage Blob Data Contributor` rights on the state storage account and `Get` access to the Key Vault secret.

