# Driver Rollback Procedure

## Summary
This runbook documents the steps for rolling back a problematic driver in a production Windows Server environment during hypercare.

## Preconditions
- You have remote administrative access to the affected VM.
- Change has been logged in the ITSM system.
- A tested fallback driver package is stored in the artifact repository.

## Detection
1. Azure Monitor alert **Driver Fault Rate High** fires for the VM resource.
2. PagerDuty incident references the failing driver version and affected host.
3. Confirm driver-related errors in Event Viewer (`System` log, source `Service Control Manager`).

## Response Steps
1. **Acknowledge Incident**
   - Accept the PagerDuty incident within the on-call schedule.
   - Update the ITSM ticket with acknowledgement time.
2. **Gather Context**
   - Run `pnputil /enum-drivers | findstr /i "<driver_name>"` to confirm installed version.
   - Capture diagnostic bundle using the platform's `collect-support-data` script.
3. **Initiate Rollback**
   - Create a restore point:
     ```powershell
     Checkpoint-Computer -Description "Pre-driver-rollback"
     ```
   - Identify the previous driver package ID:
     ```powershell
     pnputil /enum-drivers | Select-String -Pattern "<driver_name>"
     ```
   - Roll back using Device Manager CLI:
     ```powershell
     devcon rollback "PCI\\VEN_XXXX&DEV_YYYY"
     ```
4. **Validate**
   - Reboot the server during approved window.
   - Confirm the restored driver version with `pnputil`.
   - Ensure Azure Monitor alert closes automatically; otherwise manually resolve in ITSM.
5. **Communication**
   - Update incident timeline with rollback status.
   - Notify stakeholders via the hypercare Teams channel.

## Post-Incident
- Attach diagnostic bundle to ITSM record.
- Schedule problem review if alert reoccurs more than twice within 7 days.
- Trigger automation to block rollout of the faulty driver version in deployment pipelines.
