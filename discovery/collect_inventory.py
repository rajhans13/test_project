"""Collect infrastructure inventory by merging ServiceNow CMDB and Azure Migrate outputs.

This module exports servers from the ServiceNow CMDB using the Table API and merges the
result with the Azure Migrate appliance discovery export. The combined inventory is saved
as a Parquet dataset that downstream jobs (dependency resolution, scoring, etc.) can use.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

LOG = logging.getLogger(__name__)
DEFAULT_URL = "https://servicenow.example.com/api/now/table/cmdb_ci_server"
DEFAULT_LIMIT = 1000


@dataclass
class ServiceNowConfig:
    """Parameters used for querying the ServiceNow Table API."""

    url: str
    username: str
    password: str
    query: Optional[str] = None
    fields: Optional[Iterable[str]] = None
    limit: int = DEFAULT_LIMIT


def load_cmdb_from_file(path: Path) -> pd.DataFrame:
    """Load CMDB data from a JSON export saved locally."""

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    records = payload.get("result", payload)
    df = pd.DataFrame(records)
    LOG.info("Loaded %s CMDB records from %s", len(df), path)
    return df


def fetch_cmdb_inventory(config: ServiceNowConfig) -> pd.DataFrame:
    """Return CMDB records from ServiceNow as a :class:`pandas.DataFrame`.

    The function automatically paginates through the Table API using the supplied limit.
    """

    params = {"sysparm_limit": config.limit}
    if config.query:
        params["sysparm_query"] = config.query
    if config.fields:
        params["sysparm_fields"] = ",".join(config.fields)

    records = []
    offset = 0
    while True:
        params["sysparm_offset"] = offset
        LOG.debug("Requesting CMDB page offset=%s", offset)
        response = requests.get(
            config.url,
            params=params,
            auth=HTTPBasicAuth(config.username, config.password),
            timeout=60,
        )
        try:
            response.raise_for_status()
        except HTTPError as exc:  # pragma: no cover - surface in CLI
            LOG.error("ServiceNow request failed: %s", exc)
            raise

        payload = response.json()
        page_records = payload.get("result", [])
        if not page_records:
            break

        records.extend(page_records)
        LOG.debug("Fetched %s CMDB records", len(page_records))
        offset += config.limit

        if len(page_records) < config.limit:
            break

    cmdb_df = pd.DataFrame(records)
    LOG.info("Collected %s CMDB records", len(cmdb_df))
    return cmdb_df


def load_azure_migrate(path: Path) -> pd.DataFrame:
    """Load Azure Migrate appliance discovery JSON into a DataFrame."""

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    # Azure Migrate exports typically store servers under the ``Machines`` key. We fall
    # back to treating the payload as a list of host objects when the key is absent.
    if isinstance(payload, dict) and "Machines" in payload:
        records = payload["Machines"]
    else:
        records = payload

    migrate_df = pd.json_normalize(records)
    LOG.info("Loaded %s Azure Migrate discovery records", len(migrate_df))
    return migrate_df


def merge_inventory(cmdb: pd.DataFrame, migrate: pd.DataFrame) -> pd.DataFrame:
    """Merge CMDB and Azure Migrate DataFrames on FQDN."""

    if "fqdn" not in cmdb.columns:
        raise KeyError("CMDB export is missing the 'fqdn' column")
    if "fqdn" not in migrate.columns:
        raise KeyError("Azure Migrate export is missing the 'fqdn' column")

    inventory = (
        cmdb.merge(migrate, how="outer", on="fqdn", suffixes=("_cmdb", "_migrate"))
        .assign(collection_ts=pd.Timestamp.utcnow())
    )
    LOG.info("Inventory contains %s rows", len(inventory))
    return inventory


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.environ.get("SERVICENOW_URL", DEFAULT_URL),
        help="ServiceNow Table API endpoint (cmdb_ci_server table)",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("SERVICENOW_USERNAME"),
        help="Service account used to authenticate to ServiceNow",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("SERVICENOW_PASSWORD"),
        help="Service account password or token",
    )
    parser.add_argument(
        "--query",
        help="Optional sysparm_query filter to restrict CMDB records",
    )
    parser.add_argument(
        "--fields",
        nargs="*",
        help="Optional list of CMDB fields to include in the export",
    )
    parser.add_argument(
        "--cmdb-json",
        type=Path,
        help="Optional path to a CMDB JSON export for offline processing",
    )
    parser.add_argument(
        "--azure-json",
        type=Path,
        default=Path("azure_migrate_discovery.json"),
        help="Path to the Azure Migrate discovery JSON export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/landing/windows2016_inventory.parquet"),
        help="Destination Parquet file for the merged inventory",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    if args.cmdb_json:
        cmdb_df = load_cmdb_from_file(args.cmdb_json)
    else:
        if not args.username or not args.password:
            raise ValueError(
                "ServiceNow credentials are required when --cmdb-json is not supplied"
            )
        config = ServiceNowConfig(
            url=args.url,
            username=args.username,
            password=args.password,
            query=args.query,
            fields=args.fields,
        )
        cmdb_df = fetch_cmdb_inventory(config)
    migrate_df = load_azure_migrate(args.azure_json)
    inventory = merge_inventory(cmdb_df, migrate_df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_parquet(args.output, index=False)
    LOG.info("Inventory parquet written to %s", args.output)


if __name__ == "__main__":
    main()
