"""Automation helpers for deployment wave planning, change calendar updates, and Azure quota management.

This module exposes a small command line interface with three commands:

```
python -m scripts.deployment_automation assign-waves --dependencies deps.json
python -m scripts.deployment_automation update-change-calendar --dependencies deps.json \
    --freeze-windows freeze.json --approvals approvals.json --dry-run
python -m scripts.deployment_automation ensure-azure-quotas --subscription SUB --locations eastus westeurope
```

The implementation is designed to be easily integrated into CI/CD pipelines where each
step can be executed independently while sharing a consistent data model.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

import networkx as nx
import requests


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FreezeWindow:
    """Represents a deployment freeze window for a given wave."""

    wave_id: str
    start: datetime
    end: datetime
    description: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FreezeWindow":
        try:
            wave_id = str(payload["wave"])
            start = _parse_datetime(payload["start"])
            end = _parse_datetime(payload["end"])
        except KeyError as exc:  # pragma: no cover - defensive validation
            raise ValueError(f"Missing expected freeze window field: {exc}") from exc

        description = str(payload.get("description", ""))
        if end <= start:
            raise ValueError(
                f"Freeze window for {wave_id} has an end earlier than or equal to the start."
            )
        return cls(wave_id=wave_id, start=start, end=end, description=description)

    def to_serialisable(self) -> Dict[str, Any]:
        return {
            "wave": self.wave_id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
        }


@dataclass(frozen=True)
class ApprovalRecord:
    """Represents an approval captured for a specific wave."""

    wave_id: str
    approver: str
    status: str
    timestamp: datetime
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ApprovalRecord":
        try:
            wave_id = str(payload["wave"])
            approver = str(payload["approver"])
            status = str(payload["status"])
        except KeyError as exc:  # pragma: no cover - defensive validation
            raise ValueError(f"Missing expected approval field: {exc}") from exc

        timestamp = _parse_datetime(payload.get("timestamp"))
        notes = str(payload.get("notes", ""))
        return cls(wave_id=wave_id, approver=approver, status=status, timestamp=timestamp, notes=notes)

    def to_serialisable(self) -> Dict[str, Any]:
        return {
            "wave": self.wave_id,
            "approver": self.approver,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
        }


@dataclass
class ChangeRecord:
    """Aggregated change record ready to be pushed to ServiceNow."""

    wave_id: str
    applications: List[str]
    freeze_windows: List[FreezeWindow] = field(default_factory=list)
    approvals: List[ApprovalRecord] = field(default_factory=list)

    def to_servicenow_payload(self) -> Dict[str, Any]:
        """Return a payload compatible with the ServiceNow Change API."""

        window_descriptions = ", ".join(
            f"{freeze.start.isoformat()} - {freeze.end.isoformat()} ({freeze.description})"
            for freeze in self.freeze_windows
        )
        approvals_summary = "; ".join(
            f"{approval.approver}:{approval.status}"
            for approval in self.approvals
        ) or "Pending"

        return {
            "short_description": f"Deployment wave {self.wave_id} for {len(self.applications)} applications",
            "description": (
                "Applications: "
                + ", ".join(self.applications)
                + (f" | Freeze windows: {window_descriptions}" if window_descriptions else "")
                + (f" | Approvals: {approvals_summary}" if approvals_summary else "")
            ),
            "u_wave_id": self.wave_id,
            "u_applications": ",".join(self.applications),
            "u_freeze_window": window_descriptions,
            "u_approvals": approvals_summary,
        }

    def to_serialisable(self) -> Dict[str, Any]:
        return {
            "wave": self.wave_id,
            "applications": self.applications,
            "freeze_windows": [freeze.to_serialisable() for freeze in self.freeze_windows],
            "approvals": [approval.to_serialisable() for approval in self.approvals],
        }


class DependencyWavePlanner:
    """Builds dependency graphs and assigns deployment waves based on connectivity."""

    def __init__(self, dependencies: Mapping[str, Iterable[str]]):
        self._dependencies = {app: set(deps) for app, deps in dependencies.items()}

    def build_graph(self) -> nx.Graph:
        graph = nx.Graph()
        for app, deps in self._dependencies.items():
            graph.add_node(app)
            for dependency in deps:
                graph.add_node(dependency)
                graph.add_edge(app, dependency)
        return graph

    def assign_waves(self) -> Dict[str, str]:
        graph = self.build_graph()
        components = list(nx.algorithms.components.connected_components(graph))

        # Sort components to ensure deterministic wave assignment.
        components.sort(key=lambda component: sorted(component)[0])
        wave_assignments: Dict[str, str] = {}
        for index, component in enumerate(components, start=1):
            wave_id = f"wave-{index:02d}"
            for app in sorted(component):
                wave_assignments[app] = wave_id
        return wave_assignments


class ChangeCalendarManager:
    """Aggregates change data and optionally pushes it to ServiceNow."""

    def __init__(self, wave_assignments: Mapping[str, str]):
        self._wave_assignments = wave_assignments

    def build_change_records(
        self,
        freeze_windows: Sequence[FreezeWindow],
        approvals: Sequence[ApprovalRecord],
    ) -> List[ChangeRecord]:
        waves_to_apps: MutableMapping[str, List[str]] = {}
        for app, wave_id in self._wave_assignments.items():
            waves_to_apps.setdefault(wave_id, []).append(app)

        waves_to_freeze: MutableMapping[str, List[FreezeWindow]] = {}
        for window in freeze_windows:
            waves_to_freeze.setdefault(window.wave_id, []).append(window)

        waves_to_approvals: MutableMapping[str, List[ApprovalRecord]] = {}
        for approval in approvals:
            waves_to_approvals.setdefault(approval.wave_id, []).append(approval)

        change_records = []
        for wave_id, applications in sorted(waves_to_apps.items()):
            records = ChangeRecord(
                wave_id=wave_id,
                applications=sorted(applications),
                freeze_windows=sorted(
                    waves_to_freeze.get(wave_id, []), key=lambda item: item.start
                ),
                approvals=sorted(
                    waves_to_approvals.get(wave_id, []), key=lambda item: item.timestamp
                ),
            )
            change_records.append(records)
        return change_records


class ServiceNowClient:
    """Simple ServiceNow Change module client used to push change notifications."""

    def __init__(self, instance_url: str, username: str, password: str, timeout: int = 30):
        if not instance_url:
            raise ValueError("ServiceNow instance URL is required")
        self._base_url = instance_url.rstrip("/") + "/api/now/table/change_request"
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({"Content-Type": "application/json"})
        self._timeout = timeout

    def push_change(self, change_record: ChangeRecord, dry_run: bool = False) -> Dict[str, Any]:
        payload = change_record.to_servicenow_payload()
        if dry_run:
            LOGGER.info("[DRY-RUN] Would send ServiceNow payload: %s", payload)
            return {"dry_run": True, "payload": payload}

        response = self._session.post(self._base_url, json=payload, timeout=self._timeout)
        if response.status_code >= 400:
            raise RuntimeError(
                f"ServiceNow request failed with status {response.status_code}: {response.text}"
            )
        LOGGER.info(
            "ServiceNow change created for wave %s (HTTP %s)", change_record.wave_id, response.status_code
        )
        return response.json()


class AzureQuotaManager:
    """Utility to check Azure VM quota utilisation and pre-provision requests."""

    def __init__(self, subscription_id: str, dry_run: bool = False):
        if not subscription_id:
            raise ValueError("Azure subscription ID is required")
        self.subscription_id = subscription_id
        self.dry_run = dry_run

    def list_usage(self, location: str) -> List[Dict[str, Any]]:
        command = [
            "az",
            "vm",
            "list-usage",
            "--subscription",
            self.subscription_id,
            "--location",
            location,
            "--output",
            "json",
        ]
        LOGGER.debug("Executing command: %s", " ".join(command))
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(completed.stdout)

    def ensure_capacity(
        self,
        location: str,
        threshold: float = 0.8,
        buffer: float = 0.25,
    ) -> List[Dict[str, Any]]:
        usage_data = self.list_usage(location)
        requests_to_submit: List[Dict[str, Any]] = []
        for metric in usage_data:
            name = metric.get("name", {}).get("value") or metric.get("name")
            limit = metric.get("limit")
            current_value = metric.get("currentValue")

            if not isinstance(limit, (int, float)) or not isinstance(current_value, (int, float)):
                continue

            utilisation = current_value / limit if limit else 0
            LOGGER.debug(
                "Metric %s in %s has utilisation %.2f (current=%s, limit=%s)",
                name,
                location,
                utilisation,
                current_value,
                limit,
            )

            if utilisation >= threshold:
                requested_limit = int(round(limit * (1 + buffer))) or (limit + 1)
                request_payload = {
                    "location": location,
                    "metric": name,
                    "current_limit": limit,
                    "requested_limit": requested_limit,
                }
                LOGGER.info(
                    "Quota for %s in %s at %.0f%% utilisation; requesting increase to %s",
                    name,
                    location,
                    utilisation * 100,
                    requested_limit,
                )
                self.submit_quota_request(request_payload)
                requests_to_submit.append(request_payload)
        return requests_to_submit

    def submit_quota_request(self, payload: Mapping[str, Any]) -> None:
        if self.dry_run:
            LOGGER.info("[DRY-RUN] Would submit quota request: %s", payload)
            return

        command = [
            "az",
            "quota",
            "request",
            "create",
            "--subscription",
            self.subscription_id,
            "--provider",
            "Microsoft.Compute",
            "--location",
            str(payload["location"]),
            "--resource-name",
            str(payload["metric"]),
            "--value",
            str(payload["requested_limit"]),
            "--output",
            "json",
        ]
        LOGGER.debug("Executing command: %s", " ".join(command))
        subprocess.run(command, check=True, capture_output=True, text=True)


def _parse_datetime(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _load_dependencies(path: str) -> Dict[str, Set[str]]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        return {str(app): set(map(str, deps)) for app, deps in data.items()}

    if isinstance(data, list):
        dependencies: Dict[str, Set[str]] = {}
        for item in data:
            app = str(item["app"])
            deps = {str(dep) for dep in item.get("dependencies", [])}
            dependencies[app] = deps
        return dependencies

    raise TypeError("Unsupported dependency file format. Use a dict or list structure.")


def _load_freeze_windows(path: str) -> List[FreezeWindow]:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise TypeError("Freeze windows file must contain a list of objects")
    return [FreezeWindow.from_dict(item) for item in payload]


def _load_approvals(path: str) -> List[ApprovalRecord]:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise TypeError("Approvals file must contain a list of objects")
    return [ApprovalRecord.from_dict(item) for item in payload]


def _write_json(data: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, default=str)
    LOGGER.info("Wrote output to %s", path)


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign_parser = subparsers.add_parser(
        "assign-waves", help="Assign deployment waves based on application dependencies"
    )
    assign_parser.add_argument("--dependencies", required=True, help="Path to dependency JSON file")
    assign_parser.add_argument("--output", help="Optional path to write wave assignments as JSON")

    calendar_parser = subparsers.add_parser(
        "update-change-calendar", help="Build change records and push to ServiceNow"
    )
    calendar_parser.add_argument("--dependencies", required=True, help="Path to dependency JSON file")
    calendar_parser.add_argument("--freeze-windows", required=True, help="Path to freeze windows JSON file")
    calendar_parser.add_argument("--approvals", required=True, help="Path to approvals JSON file")
    calendar_parser.add_argument("--output", help="Optional path to write the change calendar JSON")
    calendar_parser.add_argument("--servicenow-instance", help="Base URL of the ServiceNow instance")
    calendar_parser.add_argument("--servicenow-user", help="ServiceNow username")
    calendar_parser.add_argument("--servicenow-password", help="ServiceNow password")
    calendar_parser.add_argument("--dry-run", action="store_true", help="Do not send data to ServiceNow")

    quota_parser = subparsers.add_parser(
        "ensure-azure-quotas", help="Check Azure VM usage and submit quota requests"
    )
    quota_parser.add_argument("--subscription", required=True, help="Azure subscription ID")
    quota_parser.add_argument("--locations", nargs="+", required=True, help="Azure regions to evaluate")
    quota_parser.add_argument("--threshold", type=float, default=0.8, help="Utilisation threshold to trigger requests")
    quota_parser.add_argument("--buffer", type=float, default=0.25, help="Buffer percentage for new quota limits")
    quota_parser.add_argument("--dry-run", action="store_true", help="Do not submit quota requests")

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if args.command == "assign-waves":
        dependencies = _load_dependencies(args.dependencies)
        planner = DependencyWavePlanner(dependencies)
        assignments = planner.assign_waves()
        LOGGER.info("Calculated wave assignments: %s", assignments)
        if args.output:
            _write_json(assignments, args.output)
        else:
            print(json.dumps(assignments, indent=2))
        return 0

    if args.command == "update-change-calendar":
        dependencies = _load_dependencies(args.dependencies)
        planner = DependencyWavePlanner(dependencies)
        assignments = planner.assign_waves()

        freeze_windows = _load_freeze_windows(args.freeze_windows)
        approvals = _load_approvals(args.approvals)

        calendar_manager = ChangeCalendarManager(assignments)
        change_records = calendar_manager.build_change_records(freeze_windows, approvals)
        serialisable = [record.to_serialisable() for record in change_records]

        if args.output:
            _write_json(serialisable, args.output)
        else:
            print(json.dumps(serialisable, indent=2))

        if args.servicenow_instance and args.servicenow_user and args.servicenow_password:
            client = ServiceNowClient(
                args.servicenow_instance,
                args.servicenow_user,
                args.servicenow_password,
            )
            for record in change_records:
                client.push_change(record, dry_run=args.dry_run)
        elif any(
            value is not None
            for value in (args.servicenow_instance, args.servicenow_user, args.servicenow_password)
        ):
            LOGGER.warning(
                "Incomplete ServiceNow credentials provided; skipping notification push."
            )
        return 0

    if args.command == "ensure-azure-quotas":
        manager = AzureQuotaManager(args.subscription, dry_run=args.dry_run)
        summary: Dict[str, List[Dict[str, Any]]] = {}
        for location in args.locations:
            summary[location] = manager.ensure_capacity(location, threshold=args.threshold, buffer=args.buffer)
        print(json.dumps(summary, indent=2))
        return 0

    parser.error(f"Unknown command {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
