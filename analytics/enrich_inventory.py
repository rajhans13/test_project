"""Enrich merged inventory with application criticality metrics from survey data."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd

LOG = logging.getLogger(__name__)
DEFAULT_SURVEY_PATH = Path("datasets/surveys/app_profile.csv")
DEFAULT_INVENTORY_PATH = Path("datasets/landing/windows2016_inventory.parquet")


PREFERRED_KEYS: Sequence[str] = (
    "application_id",
    "application",
    "business_service",
    "service_name",
)


def load_inventory(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_survey(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def determine_join_key(inventory: pd.DataFrame, survey: pd.DataFrame) -> str:
    for key in PREFERRED_KEYS:
        if key in inventory.columns and key in survey.columns:
            return key
    shared = set(inventory.columns) & set(survey.columns)
    if not shared:
        raise KeyError("Inventory and survey data share no common columns for join")
    return sorted(shared)[0]


def enrich_inventory(inventory: pd.DataFrame, survey: pd.DataFrame, join_key: str) -> pd.DataFrame:
    survey_columns = [
        col
        for col in survey.columns
        if col not in {join_key}
    ]
    LOG.debug("Joining on key '%s' with survey columns: %s", join_key, survey_columns)
    enriched = inventory.merge(survey, how="left", on=join_key)
    LOG.info("Enriched inventory with %s survey columns", len(survey_columns))
    return enriched


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="Path to the merged inventory parquet to enrich",
    )
    parser.add_argument(
        "--survey",
        type=Path,
        default=DEFAULT_SURVEY_PATH,
        help="CSV file containing application profile survey responses",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="Destination parquet file. Defaults to overwriting the input inventory",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    inventory = load_inventory(args.inventory)
    survey = load_survey(args.survey)
    join_key = determine_join_key(inventory, survey)
    enriched = enrich_inventory(inventory, survey, join_key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(args.output, index=False)
    LOG.info("Enriched inventory written to %s", args.output)


if __name__ == "__main__":
    main()
