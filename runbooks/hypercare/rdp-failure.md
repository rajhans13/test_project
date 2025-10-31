# RDP Failure Recovery

## Summary
Steps for restoring Remote Desktop access to Windows hosts during hypercare when Azure Monitor alerts for RDP connection failures.

## Preconditions
- You are the on-call engineer with PagerDuty access.
- ITSM ticket contains affected VM resource ID.
- Access to Azure Bastion or alternative console session.

## Detection
1. Azure Monitor alert **RDP Connection Failure Rate** triggers and creates an ITSM incident via webhook automation.
2. PagerDuty incident includes host name and subscription details.
3. Confirm login errors in `Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational` log.

## Response Steps
1. **Acknowledge and Communicate**
   - Accept PagerDuty incident and update ITSM ticket.
   - Notify stakeholders of investigation start in Teams.
2. **Validate Network Path**
   - Check NSG rules to confirm inbound TCP/3389 is allowed from jump hosts.
   - Use `Test-NetConnection -ComputerName <host> -Port 3389` from a healthy peer.
3. **Restart RDP Services**
   - Via Azure Serial Console or Bastion, run:
     ```powershell
     Get-Service TermService | Restart-Service -Force
     ```
   - If the service fails, check `gpresult /h` for policy conflicts.
4. **Reset User Sessions**
   - Enumerate sessions: `quser`.
   - Log off hung sessions: `logoff <session_id>`.
5. **Firewall Remediation**
   - Ensure Windows Firewall rule `RemoteDesktop-UserMode-In-TCP` is enabled:
     ```powershell
     Set-NetFirewallRule -DisplayGroup "Remote Desktop" -Enabled True
     ```
6. **Re-test Connectivity**
   - From support workstation, confirm RDP login succeeds.
   - Validate Azure Monitor alert auto-resolves; otherwise close manually with notes.

## Post-Incident
- Document root cause in ITSM and update problem backlog if recurrence >2/week.
- Capture lessons learned and update automation backlog for persistent issues.
- Verify Bastion session cleanup to avoid idle costs.
