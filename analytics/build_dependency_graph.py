"""Build dependency graph from the merged inventory dataset.

The script extracts dependency relationships, creates a graph representation using
``graph_tool`` when available (falling back to ``networkx`` otherwise), emits adjacency
lists as CSV, and optionally upserts the edges into Neo4j.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

try:  # pragma: no cover - optional dependency
    from graph_tool import Graph
except Exception:  # pragma: no cover - optional dependency
    Graph = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import networkx as nx
except Exception:  # pragma: no cover - optional dependency
    nx = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency
    GraphDatabase = None  # type: ignore

LOG = logging.getLogger(__name__)


def _extract_dependency_lists(row: pd.Series, columns: Sequence[str]) -> List[str]:
    """Return list of dependency targets from the first matching column."""

    for column in columns:
        if column not in row or pd.isna(row[column]):
            continue
        value = row[column]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = [dep.strip() for dep in value.split(",") if dep.strip()]
        else:
            parsed = value

        if isinstance(parsed, dict):
            # Azure Migrate sometimes uses ``{"MachineName": {"Name": "server01"}}``
            parsed = list(parsed.values())

        if not parsed:
            continue

        if isinstance(parsed, list):
            flattened: List[str] = []
            for item in parsed:
                if isinstance(item, str):
                    flattened.append(item)
                elif isinstance(item, dict):
                    flattened.extend(
                        str(v) for k, v in item.items() if k.lower() in {"name", "fqdn"}
                    )
                else:
                    flattened.append(str(item))
            return flattened
    return []


def extract_edges(df: pd.DataFrame, source_col: str = "fqdn") -> List[Tuple[str, str]]:
    """Extract dependency edges from the inventory DataFrame."""

    dependency_columns = [
        "dependencies",
        "dependencyTargets",
        "dependency_targets",
        "machineDependencies",
        "dependencySummary",
    ]

    edges: List[Tuple[str, str]] = []
    for _, row in df.iterrows():
        source = row.get(source_col)
        if not source:
            continue
        targets = _extract_dependency_lists(row, dependency_columns)
        edges.extend((source, target) for target in targets if target)
    LOG.info("Extracted %s dependency edges", len(edges))
    return edges


def build_graph(edges: Iterable[Tuple[str, str]]):
    """Create a graph-tool or networkx graph from edges."""

    edges = list(edges)
    if Graph is not None:  # pragma: no cover - requires graph_tool runtime
        graph = Graph(directed=True)
        vertex_index = {}
        for source, target in edges:
            for node in (source, target):
                if node not in vertex_index:
                    vertex_index[node] = graph.add_vertex()
        edge_list = [(vertex_index[s], vertex_index[t]) for s, t in edges]
        graph.add_edge_list(edge_list)
        LOG.info("Constructed graph-tool graph with %s vertices", graph.num_vertices())
        return graph

    if nx is None:
        raise RuntimeError(
            "Neither graph_tool nor networkx is available. Please install one of them."
        )

    graph = nx.DiGraph()
    graph.add_edges_from(edges)
    LOG.info("Constructed networkx graph with %s nodes", graph.number_of_nodes())
    return graph


def export_adjacency_csv(edges: Iterable[Tuple[str, str]], output: Path) -> None:
    edges = list(edges)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "target"])
        writer.writerows(edges)
    LOG.info("Wrote adjacency list to %s", output)


def load_inventory(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def push_to_neo4j(edges: Iterable[Tuple[str, str]], *, uri: str, user: str, password: str) -> None:
    if GraphDatabase is None:  # pragma: no cover - optional dependency
        raise RuntimeError("neo4j Python driver is not installed")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    query = """
    UNWIND $batch AS edge
    MERGE (s:Server {name: edge.source})
    MERGE (t:Server {name: edge.target})
    MERGE (s)-[:DEPENDS_ON]->(t)
    """
    edge_list = list(edges)
    if not edge_list:
        LOG.warning("No dependency edges to push to Neo4j")
        return

    with driver.session(database=os.environ.get("NEO4J_DATABASE")) as session:
        session.run(query, batch=[{"source": s, "target": t} for s, t in edge_list])
    LOG.info("Loaded %s edges into Neo4j", len(edge_list))


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("datasets/landing/windows2016_inventory.parquet"),
        help="Path to the merged inventory parquet file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/landing/dependency_edges.csv"),
        help="CSV file to receive adjacency list",
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.environ.get("NEO4J_URI"),
        help="Optional bolt URI for Neo4j ingestion",
    )
    parser.add_argument(
        "--neo4j-user",
        default=os.environ.get("NEO4J_USER"),
        help="Neo4j username",
    )
    parser.add_argument(
        "--neo4j-password",
        default=os.environ.get("NEO4J_PASSWORD"),
        help="Neo4j password",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    inventory = load_inventory(args.inventory)
    edges = extract_edges(inventory)
    build_graph(edges)  # Construct graph for validation; object is not persisted here.
    export_adjacency_csv(edges, args.output)

    if args.neo4j_uri and args.neo4j_user and args.neo4j_password:
        push_to_neo4j(edges, uri=args.neo4j_uri, user=args.neo4j_user, password=args.neo4j_password)


if __name__ == "__main__":
    main()
