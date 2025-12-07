#!/usr/bin/env -S uv run
"""
Audit all metrics available in Prometheus and identify their sources.

This script queries Prometheus to get all available metrics, categorizes them
by their source (based on metric prefixes and labels), and provides a summary.

Dependencies (managed by uv):
    - requests
    - rich

Usage:
    uv run audit_metrics.py
    uv run audit_metrics.py --json  # Output as JSON
"""

# /// script
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, List, Set
from urllib.parse import urljoin

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Prometheus endpoint
PROMETHEUS_URL = "http://localhost:9090"

# Known metric prefix patterns and their sources
METRIC_SOURCES = {
    "kube_": {
        "name": "kube-state-metrics",
        "description": "Kubernetes object state metrics",
        "job": "kube-state-metrics",
    },
    "node_": {
        "name": "node-exporter",
        "description": "Host/node hardware and OS metrics",
        "job": "node-exporter",
    },
    "container_": {
        "name": "cAdvisor",
        "description": "Container resource usage and performance metrics",
        "job": "kubelet",
    },
    "kubelet_": {
        "name": "Kubelet",
        "description": "Kubelet component metrics",
        "job": "kubelet",
    },
    "prometheus_": {
        "name": "Prometheus",
        "description": "Prometheus server self-monitoring metrics",
        "job": "prometheus",
    },
    "alertmanager_": {
        "name": "Alertmanager",
        "description": "Alertmanager metrics",
        "job": "alertmanager",
    },
    "grafana_": {
        "name": "Grafana",
        "description": "Grafana metrics",
        "job": "grafana",
    },
    "otelcol_": {
        "name": "OpenTelemetry Collector",
        "description": "OTel Collector metrics",
        "job": "gateway-collector",
    },
    "up": {
        "name": "Prometheus",
        "description": "Target up/down status (Prometheus internal)",
        "job": "various",
    },
    "scrape_": {
        "name": "Prometheus",
        "description": "Scrape metadata (Prometheus internal)",
        "job": "various",
    },
}

# Recording rule patterns (computed metrics)
RECORDING_RULE_PATTERNS = [
    ":",  # Recording rules typically contain colons
    "cluster:",
    "node:",
    "namespace:",
    "pod:",
]


def query_prometheus(endpoint: str) -> Dict:
    """Query Prometheus API endpoint."""
    url = urljoin(PROMETHEUS_URL, endpoint)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Prometheus: {e}", file=sys.stderr)
        sys.exit(1)


def get_all_metrics() -> List[str]:
    """Get all metric names from Prometheus."""
    data = query_prometheus("/api/v1/label/__name__/values")
    if data["status"] != "success":
        print("Failed to get metrics from Prometheus", file=sys.stderr)
        sys.exit(1)
    return sorted(data["data"])


def get_targets() -> List[Dict]:
    """Get all scrape targets from Prometheus."""
    data = query_prometheus("/api/v1/targets")
    if data["status"] != "success":
        print("Failed to get targets from Prometheus", file=sys.stderr)
        sys.exit(1)
    return data["data"]["activeTargets"]


def categorize_metrics(metrics: List[str]) -> Dict[str, List[str]]:
    """Categorize metrics by their source based on prefix."""
    categorized = defaultdict(list)

    for metric in metrics:
        # Check if it's a recording rule
        is_recording_rule = any(pattern in metric for pattern in RECORDING_RULE_PATTERNS)
        if is_recording_rule and metric not in ["up", "scrape_duration_seconds", "scrape_samples_scraped"]:
            categorized["Recording Rules"].append(metric)
            continue

        # Categorize by prefix
        categorized_flag = False
        for prefix, source_info in METRIC_SOURCES.items():
            if metric.startswith(prefix):
                categorized[source_info["name"]].append(metric)
                categorized_flag = True
                break

        # If no known prefix, put in "Other"
        if not categorized_flag:
            categorized["Other/Unknown"].append(metric)

    return dict(categorized)


def get_job_stats(targets: List[Dict]) -> Dict[str, Dict]:
    """Get statistics about scrape jobs."""
    job_stats = defaultdict(lambda: {"count": 0, "up": 0, "endpoints": []})

    for target in targets:
        job = target["labels"].get("job", "unknown")
        job_stats[job]["count"] += 1
        if target["health"] == "up":
            job_stats[job]["up"] += 1

        # Store endpoint info
        endpoint = target["scrapeUrl"]
        job_stats[job]["endpoints"].append({
            "url": endpoint,
            "health": target["health"],
            "labels": target["labels"],
        })

    return dict(job_stats)


def print_summary(categorized: Dict[str, List[str]], job_stats: Dict[str, Dict], console: Console):
    """Print a rich formatted summary."""

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Prometheus Metrics Audit[/bold cyan]\n"
        f"[dim]Querying: {PROMETHEUS_URL}[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Metrics by Source
    table = Table(title="Metrics by Source", show_header=True, header_style="bold magenta")
    table.add_column("Source", style="cyan", width=30)
    table.add_column("Count", justify="right", style="green")
    table.add_column("Description", style="dim")

    total_metrics = 0
    for source, metrics in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(metrics)
        total_metrics += count

        # Find description from METRIC_SOURCES
        description = ""
        for prefix, info in METRIC_SOURCES.items():
            if info["name"] == source:
                description = info["description"]
                break

        if source == "Recording Rules":
            description = "Pre-computed metrics from other metrics"
        elif source == "Other/Unknown":
            description = "Metrics with non-standard prefixes"

        table.add_row(source, str(count), description)

    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_metrics}[/bold]", "", style="bold")
    console.print(table)
    console.print()

    # Scrape Targets
    targets_table = Table(title="Scrape Targets (Jobs)", show_header=True, header_style="bold magenta")
    targets_table.add_column("Job", style="cyan", width=40)
    targets_table.add_column("Targets", justify="right", style="green")
    targets_table.add_column("Up", justify="right", style="green")
    targets_table.add_column("Health", justify="center")

    for job, stats in sorted(job_stats.items()):
        health = "✓" if stats["up"] == stats["count"] else "✗"
        health_style = "green" if stats["up"] == stats["count"] else "red"
        targets_table.add_row(
            job,
            str(stats["count"]),
            str(stats["up"]),
            f"[{health_style}]{health}[/{health_style}]"
        )

    console.print(targets_table)
    console.print()

    # Sample metrics from each category
    console.print(Panel.fit("[bold]Sample Metrics by Source[/bold]", border_style="blue"))
    for source, metrics in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        if metrics:
            console.print(f"\n[bold cyan]{source}[/bold cyan] ({len(metrics)} metrics)")
            # Show first 5 metrics as examples
            for metric in metrics[:5]:
                console.print(f"  • [dim]{metric}[/dim]")
            if len(metrics) > 5:
                console.print(f"  [dim]... and {len(metrics) - 5} more[/dim]")

    console.print()

    # Educational note
    note = """
## How Metrics Flow to Prometheus

All metrics you see **are stored in Prometheus**, but they originate from different sources:

1. **Prometheus scrapes targets** via HTTP (pull model) using ServiceMonitors
2. **Each target exposes `/metrics`** endpoint in Prometheus text format
3. **Metric prefixes indicate the source**:
   - `kube_*` → kube-state-metrics (watches K8s API)
   - `node_*` → node-exporter (host metrics)
   - `container_*` → cAdvisor in kubelet (container metrics)
   - `otelcol_*` → OpenTelemetry Collector
4. **Recording rules** create new metrics by computing from existing ones

To see where a specific metric comes from, check the `job` label in Prometheus!
"""
    console.print(Panel(Markdown(note), title="[bold]Understanding Metric Sources[/bold]", border_style="yellow"))


def print_json(categorized: Dict[str, List[str]], job_stats: Dict[str, Dict]):
    """Print results as JSON."""
    output = {
        "prometheus_url": PROMETHEUS_URL,
        "total_metrics": sum(len(metrics) for metrics in categorized.values()),
        "metrics_by_source": {
            source: {
                "count": len(metrics),
                "metrics": metrics
            }
            for source, metrics in categorized.items()
        },
        "scrape_targets": {
            job: {
                "target_count": stats["count"],
                "up_count": stats["up"],
                "endpoints": stats["endpoints"]
            }
            for job, stats in job_stats.items()
        }
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Audit Prometheus metrics and identify sources")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--show-all", action="store_true", help="Show all metrics (not just samples)")
    args = parser.parse_args()

    console = Console()

    if not args.json:
        console.print("[dim]Querying Prometheus...[/dim]")

    # Get all metrics and targets
    metrics = get_all_metrics()
    targets = get_targets()

    # Categorize and analyze
    categorized = categorize_metrics(metrics)
    job_stats = get_job_stats(targets)

    # Output
    if args.json:
        print_json(categorized, job_stats)
    else:
        print_summary(categorized, job_stats, console)

        if args.show_all:
            console.print("\n[bold]All Metrics:[/bold]")
            for metric in metrics:
                console.print(f"  {metric}")


if __name__ == "__main__":
    main()
