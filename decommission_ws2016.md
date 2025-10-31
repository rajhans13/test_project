# WS2016 Decommission Checklist

This runbook captures the tasks required to fully retire the Windows Server 2016 virtual machines.

## 1. Terraform Destroy Plan
1. Confirm the stabilization window has closed and no new incidents are raised.
2. In the infrastructure-as-code repository, set the workspace or backend to the WS2016 environment.
3. Run a targeted destroy plan to validate no residual dependencies remain:
   ```bash
   terraform plan -destroy -target=module.ws2016_vms
   ```
4. Review the plan output for:
   * Dependent resources such as load balancers, security groups, or shared volumes.
   * State drift warnings or resources not governed by Terraform.
5. Resolve any dependencies that block the destroy operation (re-point workloads, detach shared resources, etc.).
6. Once clean, execute the destroy and capture the plan output for audit:
   ```bash
   terraform destroy -target=module.ws2016_vms
   ```

## 2. Azure Disk Cleanup & CMDB Update
1. Enumerate residual managed disks or snapshots tagged to the retired VMs.
2. Use the asynchronous delete to purge them:
   ```bash
   az disk delete --name <disk_name> --resource-group <rg_name> --no-wait --yes
   az snapshot delete --name <snapshot_name> --resource-group <rg_name> --no-wait
   ```
3. Validate deletions via `az disk list` / `az snapshot list`.
4. Update the CMDB entry for each asset to `retired`, attaching evidence of the deletion commands and timestamps.

## 3. Contract & License Retirement
1. Inventory all support contracts, maintenance renewals, and licenses associated with Windows Server 2016 assets.
2. Submit termination or non-renewal notices to vendors and capture acknowledgement.
3. Update the procurement tracker with:
   * Contract/license identifier.
   * Termination date and confirmation reference.
   * Replacement platform (if any).
4. Notify finance and vendor-management teams of the completion status.

## Evidence & Approvals
* Archive Terraform plan/destroy logs in the change record.
* Capture Azure CLI output confirming disk/snapshot deletions.
* Store vendor termination confirmations alongside the procurement tracker entry.

Completion of the above steps finalizes the WS2016 retirement.
