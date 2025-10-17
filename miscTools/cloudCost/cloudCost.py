"""Command-line utility for comparing AWS and Azure cloud spend."""
from __future__ import annotations

import argparse
import datetime as _dt
import logging
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryAggregation,
    QueryDataset,
    QueryDefinition,
    QueryTimePeriod,
)
import matplotlib.pyplot as plt


LOGGER = logging.getLogger("cloud_cost")


@dataclass(frozen=True)
class CostWindow:
    """Defines the start/end ISO dates used for cloud cost queries."""

    start: str
    end: str

    @classmethod
    def last_full_month(cls, today: Optional[_dt.date] = None) -> "CostWindow":
        today = today or _dt.date.today()
        first_of_month = today.replace(day=1)
        end_date = first_of_month - _dt.timedelta(days=1)
        start_date = end_date.replace(day=1)
        return cls(start=start_date.isoformat(), end=(end_date + _dt.timedelta(days=1)).isoformat())


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Build the CLI argument parser for the tool."""

    window = CostWindow.last_full_month()
    parser = argparse.ArgumentParser(
        description="Fetch comparative AWS and Azure cost data for a time window.",
    )
    parser.add_argument(
        "--providers",
        default="all",
        choices=["all", "aws", "azure"],
        help="Select which providers to query. Defaults to all supported providers.",
    )
    parser.add_argument(
        "--start",
        default=window.start,
        help="ISO-8601 start date (inclusive). Defaults to the first day of the previous full month.",
    )
    parser.add_argument(
        "--end",
        default=window.end,
        help="ISO-8601 end date (exclusive). Defaults to the first day of the current month.",
    )
    parser.add_argument(
        "--granularity",
        default="MONTHLY",
        choices=["DAILY", "MONTHLY"],
        help="Aggregation granularity supported by AWS Cost Explorer and Azure Cost Management.",
    )
    parser.add_argument(
        "--aws-profile",
        help="Optional AWS shared credentials/CLI profile name.",
    )
    parser.add_argument(
        "--azure-subscription",
        help="Azure subscription ID. Defaults to the AZURE_SUBSCRIPTION_ID environment variable.",
    )
    parser.add_argument(
        "--azure-scope",
        help=(
            "Custom Azure scope (e.g., /subscriptions/<id> or /subscriptions/<id>/resourceGroups/<name>). "
            "Overrides --azure-subscription when provided."
        ),
    )
    parser.add_argument(
        "--chart",
        help="Optional output path for a comparison bar chart (PNG).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g., INFO, DEBUG).",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable matplotlib chart generation even when --chart is supplied.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s: %(message)s")


def fetch_aws_cost(start: str, end: str, granularity: str = "MONTHLY", profile: Optional[str] = None) -> float:
    """Query AWS Cost Explorer for unblended spend and return the aggregated cost."""

    LOGGER.debug("Querying AWS Cost Explorer", extra={"start": start, "end": end, "granularity": granularity, "profile": profile})
    session_kwargs: Dict[str, str] = {}
    if profile:
        session_kwargs["profile_name"] = profile
    session = boto3.Session(**session_kwargs)
    client = session.client("ce")
    try:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
        )
    except (BotoCoreError, ClientError) as exc:
        LOGGER.error("AWS Cost Explorer query failed: %s", exc)
        raise

    total = 0.0
    for result in response.get("ResultsByTime", []):
        amount = result.get("Total", {}).get("UnblendedCost", {}).get("Amount", "0")
        try:
            total += float(amount)
        except ValueError:
            LOGGER.debug("Skipping unparsable AWS amount", extra={"amount": amount})
    LOGGER.info("AWS spend from %s to %s: %.2f", start, end, total)
    return total


def _azure_granularity(granularity: str) -> str:
    return "Monthly" if granularity.upper() == "MONTHLY" else "Daily"


def fetch_azure_cost(
    start: str,
    end: str,
    granularity: str = "MONTHLY",
    subscription_id: Optional[str] = None,
    scope: Optional[str] = None,
) -> float:
    """Query Azure Cost Management for pretax cost and return the aggregated cost."""

    if not scope:
        subscription_id = subscription_id or _get_subscription_from_env()
        if not subscription_id:
            raise ValueError("An Azure subscription ID or scope must be provided.")
        scope = f"/subscriptions/{subscription_id}"

    LOGGER.debug(
        "Querying Azure Cost Management",
        extra={"start": start, "end": end, "granularity": granularity, "scope": scope},
    )

    credential = DefaultAzureCredential()
    client = CostManagementClient(credential)
    query_definition = QueryDefinition(
        type="Usage",
        timeframe="Custom",
        time_period=QueryTimePeriod(from_property=start, to=end),
        dataset=QueryDataset(
            granularity=_azure_granularity(granularity),
            aggregation={"totalCost": QueryAggregation(name="PreTaxCost", function="Sum")},
        ),
    )
    try:
        result = client.query.usage(scope=scope, parameters=query_definition)
    except AzureError as exc:
        LOGGER.error("Azure Cost Management query failed: %s", exc)
        raise

    total = 0.0
    if result.rows:
        try:
            cost_index = next(
                index for index, column in enumerate(result.columns or []) if getattr(column, "name", "") == "PreTaxCost"
            )
        except StopIteration:
            cost_index = 0
        for row in result.rows:
            try:
                total += float(row[cost_index])
            except (ValueError, IndexError) as exc:
                LOGGER.debug("Skipping Azure row", extra={"row": row, "error": str(exc)})
    LOGGER.info("Azure spend from %s to %s: %.2f", start, end, total)
    return total


def _get_subscription_from_env() -> Optional[str]:
    import os

    return os.environ.get("AZURE_SUBSCRIPTION_ID")


def build_chart(values: Dict[str, float], output_path: str) -> None:
    LOGGER.debug("Generating chart", extra={"output_path": output_path, "values": values})
    providers = list(values.keys())
    costs = [values[p] for p in providers]
    plt.figure(figsize=(6, 4))
    plt.bar(providers, costs, color=["#ff9900" if p == "AWS" else "#008ad7" for p in providers])
    plt.ylabel("Cost (USD)")
    plt.title("Cloud spend comparison")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    LOGGER.info("Chart written to %s", output_path)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log_level)

    LOGGER.debug("CLI arguments parsed", extra={"args": vars(args)})

    provider_targets = {"aws", "azure"} if args.providers == "all" else {args.providers}
    costs: Dict[str, float] = {}

    if "aws" in provider_targets:
        costs["AWS"] = fetch_aws_cost(args.start, args.end, args.granularity, profile=args.aws_profile)

    if "azure" in provider_targets:
        costs["Azure"] = fetch_azure_cost(
            args.start,
            args.end,
            args.granularity,
            subscription_id=args.azure_subscription,
            scope=args.azure_scope,
        )

    if args.chart and not args.no_plot:
        try:
            build_chart(costs, args.chart)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Failed to create chart: %s", exc)
            return 1

    for provider, amount in costs.items():
        print(f"{provider}: ${amount:,.2f}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
