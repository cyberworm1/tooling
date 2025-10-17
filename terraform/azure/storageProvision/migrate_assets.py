"""CLI utility for migrating local assets into Azure Blob Storage containers."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional

from azure.core.exceptions import AzureError, ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


LOGGER = logging.getLogger("migrate_assets")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload local files to an Azure Blob Storage container.")
    parser.add_argument("--source", required=True, help="Local directory containing assets to upload.")
    parser.add_argument("--account", required=True, help="Target storage account name.")
    parser.add_argument("--container", required=True, help="Destination container name.")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Number of upload retries per file before failing (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and log files without uploading them.",
    )
    parser.add_argument(
        "--create-container",
        action="store_true",
        help="Create the container if it does not exist.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g., INFO, DEBUG).",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s: %(message)s")


def _iter_files(source: Path) -> Iterable[Path]:
    for path in source.rglob("*"):
        if path.is_file():
            yield path


def migrate_assets(
    source: Path,
    account: str,
    container: str,
    *,
    dry_run: bool = False,
    max_retries: int = 3,
    create_container: bool = False,
) -> None:
    credential = DefaultAzureCredential()
    service_client = BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=credential,
    )
    container_client = service_client.get_container_client(container)

    if create_container:
        try:
            container_client.create_container()
            LOGGER.info("Created container %s", container)
        except ResourceExistsError:
            LOGGER.debug("Container %s already exists", container)

    if dry_run:
        LOGGER.info("Running in dry-run mode; no uploads will be performed.")

    total_files = 0
    uploaded = 0

    for file_path in _iter_files(source):
        total_files += 1
        blob_path = file_path.relative_to(source).as_posix()
        LOGGER.debug("Processing %s", blob_path)
        if dry_run:
            continue

        for attempt in range(1, max_retries + 1):
            try:
                with file_path.open("rb") as data:
                    container_client.upload_blob(
                        name=blob_path,
                        data=data,
                        overwrite=True,
                        max_concurrency=4,
                    )
                uploaded += 1
                LOGGER.info("Uploaded %s", blob_path)
                break
            except AzureError as exc:
                LOGGER.warning("Attempt %s failed for %s: %s", attempt, blob_path, exc)
                if attempt == max_retries:
                    raise

    LOGGER.info("Processed %s files; uploaded %s blobs.", total_files, uploaded)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log_level)

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists() or not source_path.is_dir():
        LOGGER.error("Source directory does not exist: %s", source_path)
        return 1

    try:
        migrate_assets(
            source_path,
            args.account,
            args.container,
            dry_run=args.dry_run,
            max_retries=args.max_retries,
            create_container=args.create_container,
        )
    except AzureError as exc:
        LOGGER.error("Upload failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
