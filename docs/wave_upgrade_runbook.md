# Wave Upgrade Runbook

This runbook codifies the actions requested for the wave-based upgrade flow. It
is paired with the [`scripts/wave_upgrade.py`](../scripts/wave_upgrade.py)
automation helper.

## Prerequisites

* Azure CLI with the Azure DevOps extension installed (`az extension add --name
  azure-devops`).
* Logged in to the correct Azure subscription and DevOps organisation (`az
  login` and `az devops configure --defaults org=... project=...`).
* Sufficient permissions to lock branches, trigger pipelines, and run Azure
  Backup snapshots.
* Smoke and compliance commands accessible from the execution host.

## Usage

```bash
python scripts/wave_upgrade.py 03 \
  --org-url https://dev.azure.com/contoso \
  --project platform-upgrades \
  --repository core-app \
  --branch release/wave-03 \
  --pipeline-name core-app-upgrade \
  --wave-variable-group wave_03_vg \
  --backup-vault contoso-upgrade-vault \
  --backup-resource-group rg-upgrade-backups \
  --vm app-01 \
  --vm app-02 \
  --smoke-test pytest smoke/ \
  --compliance python scripts/config_check.py \
  --traffic-switch az network traffic-manager endpoint update --name web \
  --approval alice@contoso.com \
  --approval bob@contoso.com \
  --execute
```

Run without `--execute` to perform a dry-run and validate the command surface
before touching production.

## Workflow Summary

1. **Change Freeze** – the script locks the specified branch in Azure DevOps and
   immediately triggers Azure Backup snapshots for each listed VM.
2. **Upgrade Invocation** – the upgrade pipeline is queued with the
   `wave_03_vg` variable group. The run is monitored until completion.
3. **Post-Upgrade Validation** – smoke and configuration compliance scripts are
   executed. Traffic switch logic is only reached when both checks succeed.
4. **Reporting and Sign-off** – a `datasets/reports/wave_<id>_summary.csv`
   report is appended with the run metadata. Approver identities specified via
   `--approval` are recorded for audit purposes.

Refer to the generated CSV for the authoritative history of wave executions.
