# Training Workshops Plan

This document outlines the required training workshops for ASUK Operations and DevOps personnel. Publish the finalized agenda, recordings, and materials to the internal LMS following each session.

## Objectives
- Familiarize teams with the updated CI/CD pipeline and Terraform infrastructure changes.
- Provide hands-on practice with deployment, rollback, and monitoring workflows.
- Capture feedback to refine documentation and tooling.

## Workshop Schedule
| Session | Audience | Duration | Delivery | Key Topics | Artefacts to Upload |
| --- | --- | --- | --- | --- | --- |
| 1. Platform Overview & Pipeline Deep Dive | Ops & DevOps | 2 hours | Live virtual session | CI/CD stages, promotion strategy, Confluence runbook walkthrough | Slide deck (PDF), session recording (MP4), Q&A notes |
| 2. Hands-on Deployment & Rollback Lab | Ops & DevOps | 3 hours | Hybrid (lab environment) | Terraform apply, ArgoCD rollback, incident response drill | Lab guide (Markdown/PDF), recorded demo, lab completion checklist |
| 3. Monitoring & Troubleshooting | Ops, SRE | 1.5 hours | Live virtual | CloudWatch dashboards, alert tuning, troubleshooting scenarios | Recording, updated troubleshooting matrix, follow-up action items |

## Pre-requisites
- Confirm sandbox AWS accounts provisioned with limited IAM roles.
- Ensure participants have VPN access and kubectl configured against staging cluster.
- Share workshop calendar invites with links to preparation materials.

## Facilitation Checklist
- [ ] Dry-run session with presenters 48 hours prior.
- [ ] Prepare interactive polls/quizzes.
- [ ] Coordinate note-taker for capturing action items.
- [ ] Start recording at session kickoff and verify audio.
- [ ] After session, trim recording and upload to LMS module `ASUK Platform Enablement`.
- [ ] Update LMS metadata with date, instructors, and learning objectives.
- [ ] Notify participants via email/Slack once materials available.

## Feedback & Continuous Improvement
- Collect survey responses within 24 hours (use form `ASUK Workshop Feedback`).
- Review feedback in weekly Ops-DevOps sync; track follow-ups in Jira project `ASUKOPS`.
- Incorporate improvements into next session and Confluence documentation.

## Ownership
- **Primary Facilitator:** DevOps Enablement Lead.
- **Backup Facilitator:** Ops Shift Lead.
- **LMS Administrator:** L&D Coordinator.

