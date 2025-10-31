# CAB Minutes – 20 Feb 2025

- **Change Title:** Platform scaling waves for March 2025
- **Requested By:** Platform Operations
- **Attendees:** Release Management, Platform Engineering, ASUK Representatives (Priya Patel, Simon Grant)
- **Related Work Items:** Azure Boards #8421, #8422, #8423
- **Deployment Version:** v2025.0.1

## Discussion Summary
1. Reviewed retrospective outcomes and confirmed remediation commitments for Terraform tagging, runbook hardening, and DSC compliance beacons.
2. Demonstrated updated `create-deployment.rtf` runbook and DSC configuration with automated release markers.
3. Validated monitoring improvements scheduled under action item AI-001 from the Azure DevOps Wiki.

## Decisions
- ✅ ASUK approved proceeding with scaling waves contingent on deploying Terraform release `v2025.0.1` and verifying DSC compliance logs before each wave.
- ✅ Release Management to publish CAB summary link in Azure DevOps Wiki immediately after this meeting.
- ✅ Platform Engineering to run a dry-run deployment using the updated runbook within 48 hours.

## Follow-Up Actions
- Platform Engineering: attach Terraform plan artifacts to CAB record and notify ASUK once dry run completes.
- Release Management: maintain CAB note template in Wiki and capture attendance for subsequent meetings.
