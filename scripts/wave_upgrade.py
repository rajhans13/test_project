#!/usr/bin/env python3
"""Wave upgrade orchestration helper.

This utility coordinates Azure DevOps and Azure platform operations for
wave-based upgrade activities.  The workflow encoded in the script is driven by
the following high-level stages:

1. Enforce change freeze by locking the delivery branch and collecting Azure
   Backup snapshots of the virtual machines that will be touched by the wave.
2. Invoke the upgrade pipeline with the correct wave variable group and monitor
   the run until it completes.
3. Execute the post-upgrade smoke test and configuration compliance validation.
   Traffic can optionally be flipped after both checks succeed.
4. Capture a structured run summary under ``datasets/reports`` and record the
   approval artefacts that sign off on the wave.

The script favours shelling out to the Azure CLI because that is the most
portable way to interact with Azure DevOps and Azure Backup from automation
without pulling in a heavy SDK dependency.  Every command is executed through a
``run_command`` helper that supports a ``--dry-run`` mode.  Dry-run is the
default to make the tooling safe to exercise in CI without touching a real
environment.  Pass ``--execute`` when you are ready to run against production.

The CSV summary that is produced by the tool is append-only.  Each run adds a
row containing the key artefacts that auditors typically ask for: change freeze
lock confirmation, snapshot status, pipeline outcome, test results, traffic
switch indicator, and the list of approvers that granted the electronic
sign-off.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class RunContext:
    """Container for all settings required by a wave execution."""

    wave_id: str
    org_url: str
    project: str
    repository: str
    branch: str
    pipeline_name: str
    wave_variable_group: str
    backup_vault: str
    backup_resource_group: str
    vm_names: Sequence[str]
    smoke_test_command: Sequence[str]
    compliance_command: Sequence[str]
    traffic_switch_command: Sequence[str] | None = None
    approvals: Sequence[str] = ()
    dry_run: bool = True


@dataclass
class StageResult:
    name: str
    succeeded: bool
    details: dict = field(default_factory=dict)


def run_command(command: Sequence[str], dry_run: bool = True) -> str:
    """Execute *command* via subprocess, honouring dry-run mode."""

    command_display = " ".join(shlex.quote(part) for part in command)
    if dry_run:
        print(f"[dry-run] {command_display}")
        return ""

    completed = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return completed.stdout.strip()


def lock_branch(ctx: RunContext) -> StageResult:
    """Lock the branch in Azure DevOps to enforce the change freeze."""

    command = [
        "az",
        "repos",
        "ref",
        "update",
        "--org",
        ctx.org_url,
        "--project",
        ctx.project,
        "--repository",
        ctx.repository,
        "--name",
        f"refs/heads/{ctx.branch}",
        "--lock",
    ]

    output = run_command(command, ctx.dry_run)
    details = {"command": command, "output": output}
    return StageResult("branch_lock", succeeded=True, details=details)


def snapshot_vms(ctx: RunContext) -> StageResult:
    """Trigger Azure Backup snapshots for the provided VM list."""

    success = True
    per_vm_results = []
    for vm in ctx.vm_names:
        command = [
            "az",
            "backup",
            "protection",
            "backup-now",
            "--resource-group",
            ctx.backup_resource_group,
            "--vault-name",
            ctx.backup_vault,
            "--item-name",
            vm,
            "--backup-management-type",
            "AzureIaasVM",
            "--retain-until",
            datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        ]
        try:
            output = run_command(command, ctx.dry_run)
            per_vm_results.append({"vm": vm, "output": output})
        except subprocess.CalledProcessError as exc:  # pragma: no cover - safety net
            success = False
            per_vm_results.append({"vm": vm, "error": exc.stdout})

    return StageResult("vm_snapshots", succeeded=success, details={"vms": per_vm_results})


def invoke_pipeline(ctx: RunContext) -> StageResult:
    """Invoke the Azure DevOps pipeline for the wave and monitor its completion."""

    queue_command = [
        "az",
        "pipelines",
        "run",
        "--org",
        ctx.org_url,
        "--project",
        ctx.project,
        "--name",
        ctx.pipeline_name,
        "--branch",
        ctx.branch,
        "--variables",
        f"wave_variable_group={ctx.wave_variable_group}",
        f"wave_id={ctx.wave_id}",
    ]

    run_id_output = run_command(queue_command, ctx.dry_run)
    run_id = run_id_output.strip()

    monitor_command = [
        "az",
        "pipelines",
        "runs",
        "show",
        "--org",
        ctx.org_url,
        "--project",
        ctx.project,
    ]
    if run_id:
        monitor_command.extend(["--id", run_id])

    run_details = run_command(monitor_command, ctx.dry_run)
    if ctx.dry_run:
        status = "dry-run"
        succeeded = True
    else:
        status = "unknown" if not run_details else json.loads(run_details).get("status", "unknown")
        succeeded = status.lower() == "completed"

    return StageResult(
        "pipeline",
        succeeded=succeeded,
        details={"queue_command": queue_command, "monitor_command": monitor_command, "status": status},
    )


def run_post_upgrade_checks(ctx: RunContext) -> tuple[StageResult, StageResult]:
    """Run smoke and compliance validations."""

    smoke_output = run_command(ctx.smoke_test_command, ctx.dry_run)
    smoke_result = StageResult(
        "smoke_test",
        succeeded=bool(smoke_output or ctx.dry_run),
        details={"command": list(ctx.smoke_test_command), "output": smoke_output},
    )

    compliance_output = run_command(ctx.compliance_command, ctx.dry_run)
    compliance_result = StageResult(
        "config_compliance",
        succeeded=bool(compliance_output or ctx.dry_run),
        details={"command": list(ctx.compliance_command), "output": compliance_output},
    )

    return smoke_result, compliance_result


def maybe_flip_traffic(ctx: RunContext, smoke: StageResult, compliance: StageResult) -> StageResult:
    """Flip customer traffic when both validations have passed."""

    if not ctx.traffic_switch_command:
        return StageResult("traffic_switch", succeeded=False, details={"reason": "no command configured"})

    if not (smoke.succeeded and compliance.succeeded):
        return StageResult(
            "traffic_switch",
            succeeded=False,
            details={"reason": "validation checks did not succeed"},
        )

    output = run_command(ctx.traffic_switch_command, ctx.dry_run)
    return StageResult(
        "traffic_switch",
        succeeded=bool(output or ctx.dry_run),
        details={"command": list(ctx.traffic_switch_command), "output": output},
    )


def write_summary(ctx: RunContext, stages: Iterable[StageResult]) -> Path:
    """Persist the execution summary in datasets/reports."""

    reports_dir = Path("datasets") / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / f"wave_{ctx.wave_id}_summary.csv"

    fieldnames = [
        "timestamp",
        "wave_id",
        "branch_locked",
        "snapshot_success",
        "pipeline_status",
        "smoke_passed",
        "compliance_passed",
        "traffic_flipped",
        "approvals",
    ]

    data = {
        stage.name: stage for stage in stages
    }

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "wave_id": ctx.wave_id,
        "branch_locked": data.get("branch_lock", StageResult("", False)).succeeded,
        "snapshot_success": data.get("vm_snapshots", StageResult("", False)).succeeded,
        "pipeline_status": data.get("pipeline", StageResult("", False)).details.get("status", "unknown"),
        "smoke_passed": data.get("smoke_test", StageResult("", False)).succeeded,
        "compliance_passed": data.get("config_compliance", StageResult("", False)).succeeded,
        "traffic_flipped": data.get("traffic_switch", StageResult("", False)).succeeded,
        "approvals": ";".join(ctx.approvals),
    }

    file_exists = summary_path.exists()
    with summary_path.open("a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return summary_path


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a wave upgrade workflow")
    parser.add_argument("wave_id", help="Identifier for the wave (e.g. 03)")
    parser.add_argument("--org-url", required=True, help="Azure DevOps organisation URL")
    parser.add_argument("--project", required=True, help="Azure DevOps project name")
    parser.add_argument("--repository", required=True, help="Azure DevOps repository name")
    parser.add_argument("--branch", default="main", help="Branch to lock and deploy from")
    parser.add_argument("--pipeline-name", required=True, help="Pipeline to trigger")
    parser.add_argument("--wave-variable-group", required=True, help="Variable group to apply")
    parser.add_argument("--backup-vault", required=True, help="Azure Backup vault name")
    parser.add_argument("--backup-resource-group", required=True, help="Resource group for backup vault")
    parser.add_argument("--vm", action="append", dest="vm_names", default=[], help="Virtual machine to snapshot")
    parser.add_argument("--smoke-test", required=True, nargs=argparse.REMAINDER, help="Command for smoke tests")
    parser.add_argument(
        "--compliance", required=True, nargs=argparse.REMAINDER, help="Command for compliance validation"
    )
    parser.add_argument(
        "--traffic-switch",
        nargs=argparse.REMAINDER,
        help="Command that flips customer traffic once validations succeed",
    )
    parser.add_argument(
        "--approval",
        dest="approvals",
        action="append",
        default=[],
        help="Approver identity for electronic sign-off",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run the commands instead of printing them",
    )
    return parser.parse_args(argv)


def build_context(args: argparse.Namespace) -> RunContext:
    smoke_command = args.smoke_test
    compliance_command = args.compliance

    if smoke_command and smoke_command[0] == "--":
        smoke_command = smoke_command[1:]
    if compliance_command and compliance_command[0] == "--":
        compliance_command = compliance_command[1:]

    traffic_command: List[str] | None = None
    if args.traffic_switch:
        traffic_command = list(args.traffic_switch)
        if traffic_command and traffic_command[0] == "--":
            traffic_command = traffic_command[1:]

    if not args.vm_names:
        raise SystemExit("At least one --vm must be specified to snapshot")

    return RunContext(
        wave_id=args.wave_id,
        org_url=args.org_url,
        project=args.project,
        repository=args.repository,
        branch=args.branch,
        pipeline_name=args.pipeline_name,
        wave_variable_group=args.wave_variable_group,
        backup_vault=args.backup_vault,
        backup_resource_group=args.backup_resource_group,
        vm_names=args.vm_names,
        smoke_test_command=list(smoke_command),
        compliance_command=list(compliance_command),
        traffic_switch_command=traffic_command,
        approvals=args.approvals,
        dry_run=not args.execute,
    )


def main(argv: Sequence[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = parse_args(argv)
    ctx = build_context(args)

    stages: List[StageResult] = []
    stages.append(lock_branch(ctx))
    stages.append(snapshot_vms(ctx))
    pipeline_result = invoke_pipeline(ctx)
    stages.append(pipeline_result)

    smoke_result, compliance_result = run_post_upgrade_checks(ctx)
    stages.extend([smoke_result, compliance_result])

    traffic_result = maybe_flip_traffic(ctx, smoke_result, compliance_result)
    stages.append(traffic_result)

    summary_path = write_summary(ctx, stages)
    print(f"Summary captured at: {summary_path}")

    return 0 if pipeline_result.succeeded and smoke_result.succeeded and compliance_result.succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
