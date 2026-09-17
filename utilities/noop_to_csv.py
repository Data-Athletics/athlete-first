#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert a NOOP .noopbak backup into one analysis-ready CSV.

The exporter reads the backup without modifying it and combines NOOP's decoded
sensor tables into a long-format CSV. Columns that do not apply to a given
stream are left blank. Suspicious timestamps are retained and labeled unless
--only-plausible is supplied.

Examples:
    uv run noop_to_csv.py noop-backup-20260904-153516.noopbak
    uv run noop_to_csv.py backup.noopbak -o device-data.csv
    uv run noop_to_csv.py backup.noopbak --only-plausible
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from collections import Counter
from collections.abc import Iterator
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

MIN_PLAUSIBLE_UNIX_S = 1_700_000_000
FUTURE_MARGIN_S = 86_400

CSV_FIELDS = [
    "backup_file",
    "noop_schema_version",
    "backup_exported_at_utc",
    "device_id",
    "unix_s",
    "iso_utc",
    "timestamp_status",
    "stream",
    "source_table",
    "hr_bpm",
    "rr_ms",
    "rr_instant_bpm",
    "rr_seq",
    "rr_ord",
    "rr_source_channel",
    "rr_stored_ts_suspect",
    "gravity_x",
    "gravity_y",
    "gravity_z",
    "gravity_vector_magnitude_g",
    "gravity_dynamic_accel_g",
    "ppg_bpm",
    "ppg_conf",
    "spo2_red_raw",
    "spo2_ir_raw",
    "skin_temp_raw",
    "skin_temp_aux1_raw",
    "skin_temp_aux2_raw",
    "resp_raw",
    "step_counter",
    "step_activity_class",
    "sleep_state",
    "sleep_state_raw_byte",
    "battery_soc_pct",
    "battery_mv",
    "battery_charging",
    "event_kind",
    "event_payload_json",
    "synced",
]

TEXT_FIELDS = {
    "backup_file",
    "backup_exported_at_utc",
    "device_id",
    "iso_utc",
    "timestamp_status",
    "stream",
    "source_table",
    "event_kind",
    "event_payload_json",
}

# Each mapping is database-column -> CSV-column. All entries are optional except
# deviceId and ts, which are checked separately to tolerate future schema changes.
STREAM_SPECS = (
    {
        "table": "hrSample",
        "stream": "heart_rate",
        "columns": {"bpm": "hr_bpm", "synced": "synced"},
        "tie": (),
    },
    {
        "table": "rrInterval",
        "stream": "rr_interval",
        "columns": {
            "rrMs": "rr_ms",
            "seq": "rr_seq",
            "ord": "rr_ord",
            "srcChannel": "rr_source_channel",
            "tsSuspect": "rr_stored_ts_suspect",
            "synced": "synced",
        },
        "tie": ("ord", "seq", "rrMs"),
    },
    {
        "table": "gravitySample",
        "stream": "gravity",
        "columns": {
            "x": "gravity_x",
            "y": "gravity_y",
            "z": "gravity_z",
            "dynAccel": "gravity_dynamic_accel_g",
            "synced": "synced",
        },
        "tie": (),
    },
    {
        "table": "ppgHrSample",
        "stream": "ppg_heart_rate",
        "columns": {"bpm": "ppg_bpm", "conf": "ppg_conf"},
        "tie": (),
    },
    {
        "table": "spo2Sample",
        "stream": "optical_raw",
        "columns": {
            "red": "spo2_red_raw",
            "ir": "spo2_ir_raw",
            "synced": "synced",
        },
        "tie": (),
    },
    {
        "table": "skinTempSample",
        "stream": "skin_temperature_raw",
        "columns": {
            "raw": "skin_temp_raw",
            "aux1Raw": "skin_temp_aux1_raw",
            "aux2Raw": "skin_temp_aux2_raw",
            "synced": "synced",
        },
        "tie": (),
    },
    {
        "table": "respSample",
        "stream": "respiration_raw",
        "columns": {"raw": "resp_raw", "synced": "synced"},
        "tie": (),
    },
    {
        "table": "stepSample",
        "stream": "steps",
        "columns": {
            "counter": "step_counter",
            "activityClass": "step_activity_class",
        },
        "tie": (),
    },
    {
        "table": "sleepStateSample",
        "stream": "sleep_state",
        "columns": {
            "state": "sleep_state",
            "rawByte": "sleep_state_raw_byte",
        },
        "tie": (),
    },
    {
        "table": "battery",
        "stream": "battery",
        "columns": {
            "soc": "battery_soc_pct",
            "mv": "battery_mv",
            "charging": "battery_charging",
            "synced": "synced",
        },
        "tie": (),
    },
    {
        "table": "event",
        "stream": "event",
        "columns": {
            "kind": "event_kind",
            "payloadJSON": "event_payload_json",
            "synced": "synced",
        },
        "tie": ("kind",),
    },
)


class ConversionError(RuntimeError):
    """A concise, user-facing conversion error."""


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def load_json_bytes(raw: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConversionError(f"Could not read {source}: {exc}") from exc
    return value if isinstance(value, dict) else {}


def find_archive_member(
    archive: zipfile.ZipFile, names: tuple[str, ...]
) -> zipfile.ZipInfo | None:
    wanted = {name.lower() for name in names}
    matches = [
        item
        for item in archive.infolist()
        if not item.is_dir() and PurePosixPath(item.filename).name.lower() in wanted
    ]
    return matches[0] if matches else None


def extract_database(archive: zipfile.ZipFile, destination: Path) -> Path:
    candidates = [
        item
        for item in archive.infolist()
        if not item.is_dir()
        and PurePosixPath(item.filename).suffix.lower()
        in {".sqlite", ".sqlite3", ".db"}
    ]
    preferred = [
        item
        for item in candidates
        if PurePosixPath(item.filename).name.lower() == "noop-backup.sqlite"
    ]
    if len(preferred) == 1:
        selected = preferred[0]
    elif len(candidates) == 1:
        selected = candidates[0]
    elif not candidates:
        raise ConversionError("The backup does not contain a SQLite database.")
    else:
        names = ", ".join(item.filename for item in candidates)
        raise ConversionError(f"The backup contains multiple databases: {names}")

    if selected.file_size == 0:
        raise ConversionError("The SQLite database inside the backup is empty.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(selected, "r") as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target)
    return destination


def load_manifest_from_archive(archive: zipfile.ZipFile) -> dict[str, Any]:
    member = find_archive_member(archive, ("manifest.json",))
    if member is None:
        return {}
    return load_json_bytes(archive.read(member), member.filename)


def load_manifest_next_to_database(database_path: Path) -> dict[str, Any]:
    manifest_path = database_path.with_name("manifest.json")
    if not manifest_path.is_file():
        return {}
    try:
        return load_json_bytes(manifest_path.read_bytes(), str(manifest_path))
    except OSError as exc:
        raise ConversionError(f"Could not read {manifest_path}: {exc}") from exc


def exported_at_seconds(manifest: dict[str, Any]) -> float | None:
    value = manifest.get("exportedAt")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        return None
    if seconds >= 10_000_000_000:
        seconds /= 1000.0
    return seconds


def iso_utc(seconds: float | None) -> str:
    if seconds is None:
        return ""
    try:
        return (
            datetime.fromtimestamp(float(seconds), UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
    except OverflowError, OSError, ValueError:
        return ""


def normalize_timestamp(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def timestamp_status(seconds: float | None, reference_seconds: float | None) -> str:
    if seconds is None or not iso_utc(seconds):
        return "invalid_timestamp"
    if seconds < MIN_PLAUSIBLE_UNIX_S:
        return "implausible_before_2023-11"
    if reference_seconds is not None and seconds > reference_seconds + FUTURE_MARGIN_S:
        return "implausible_after_export_plus_1d"
    if reference_seconds is None:
        return "plausible_lower_bound_only"
    return "plausible_by_noop_bounds"


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    statement = f"PRAGMA table_info({quote_identifier(table)})"
    return {str(row[1]) for row in connection.execute(statement)}


def sqlite_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }


def blank_row() -> dict[str, Any]:
    return {field: "" for field in CSV_FIELDS}


def is_real_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def enrich_row(table: str, row: dict[str, Any]) -> None:
    if table == "rrInterval":
        rr_ms = row.get("rr_ms")
        if is_real_number(rr_ms) and float(rr_ms) > 0:
            row["rr_instant_bpm"] = round(60_000.0 / float(rr_ms), 2)
    elif table == "gravitySample":
        values = [row.get("gravity_x"), row.get("gravity_y"), row.get("gravity_z")]
        if all(is_real_number(value) for value in values):
            row["gravity_vector_magnitude_g"] = round(
                math.sqrt(sum(float(value) ** 2 for value in values)), 6
            )


def safe_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # Protect people who open the CSV in spreadsheet software. The original
    # database remains unchanged, and the apostrophe is visible on re-import.
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def stream_rows(
    connection: sqlite3.Connection,
    spec: dict[str, Any],
    stream_order: int,
    reference_seconds: float | None,
    metadata: dict[str, Any],
) -> Iterator[tuple[tuple[Any, ...], dict[str, Any]]]:
    table = str(spec["table"])
    available = table_columns(connection, table)
    if not {"deviceId", "ts"}.issubset(available):
        return

    mapping: dict[str, str] = spec["columns"]
    selected = ["deviceId", "ts"] + [name for name in mapping if name in available]
    order_columns = ["ts", "deviceId"] + [
        name for name in spec["tie"] if name in available
    ]
    query = (
        "SELECT "
        + ", ".join(quote_identifier(name) for name in selected)
        + f" FROM {quote_identifier(table)} ORDER BY "
        + ", ".join(quote_identifier(name) for name in order_columns)
    )

    cursor = connection.execute(query)
    for source_row in cursor:
        record = blank_row()
        record.update(metadata)
        record["device_id"] = source_row["deviceId"]
        seconds = normalize_timestamp(source_row["ts"])
        record["unix_s"] = "" if seconds is None else seconds
        record["iso_utc"] = iso_utc(seconds)
        record["timestamp_status"] = timestamp_status(seconds, reference_seconds)
        record["stream"] = spec["stream"]
        record["source_table"] = table
        for database_column, csv_column in mapping.items():
            if database_column in selected:
                value = source_row[database_column]
                record[csv_column] = "" if value is None else value
        enrich_row(table, record)

        invalid_sort = 1 if seconds is None else 0
        timestamp_sort = 0 if seconds is None else float(seconds)
        tie_sort = tuple(str(source_row[name]) for name in order_columns[2:])
        sort_key = (
            invalid_sort,
            timestamp_sort,
            stream_order,
            str(source_row["deviceId"]),
            *tie_sort,
        )
        yield sort_key, record


def write_csv(
    connection: sqlite3.Connection,
    output_path: Path,
    manifest: dict[str, Any],
    input_name: str,
    only_plausible: bool,
    force: bool,
) -> tuple[int, int, Counter[str], list[str]]:
    if output_path.exists() and not force:
        raise ConversionError(
            f"Output already exists: {output_path}. Use --force to replace it."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tables = sqlite_tables(connection)
    recognized = [spec for spec in STREAM_SPECS if spec["table"] in tables]
    if not recognized:
        raise ConversionError("No supported decoded sensor tables were found.")

    reference_seconds = exported_at_seconds(manifest)
    metadata = {
        "backup_file": input_name,
        "noop_schema_version": manifest.get("schemaVersion", ""),
        "backup_exported_at_utc": iso_utc(reference_seconds),
    }
    generators = [
        stream_rows(connection, spec, index, reference_seconds, metadata)
        for index, spec in enumerate(recognized)
    ]

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    written = 0
    flagged = 0
    stream_counts: Counter[str] = Counter()
    try:
        with temporary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(CSV_FIELDS)
            for _, record in heapq.merge(*generators, key=lambda item: item[0]):
                plausible = str(record["timestamp_status"]).startswith("plausible_")
                if not plausible:
                    flagged += 1
                    if only_plausible:
                        continue
                writer.writerow(
                    [
                        safe_text(record[field])
                        if field in TEXT_FIELDS
                        else record[field]
                        for field in CSV_FIELDS
                    ]
                )
                written += 1
                stream_counts[str(record["stream"])] += 1
        os.replace(temporary_path, output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise

    missing_tables = [
        str(spec["table"]) for spec in STREAM_SPECS if spec["table"] not in tables
    ]
    return written, flagged, stream_counts, missing_tables


def validate_database(connection: sqlite3.Connection) -> None:
    result = connection.execute("PRAGMA quick_check").fetchone()
    if result is None or result[0] != "ok":
        detail = "unknown error" if result is None else str(result[0])
        raise ConversionError(f"SQLite integrity check failed: {detail}")


def connect_read_only(database_path: Path) -> sqlite3.Connection:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def convert(args: argparse.Namespace) -> int:
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        raise ConversionError(f"Input file not found: {input_path}")

    output_path = (
        args.output.expanduser().resolve()
        if args.output is not None
        else input_path.with_name(f"{input_path.stem}-decoded.csv")
    )
    if output_path == input_path:
        raise ConversionError("Input and output paths must be different.")

    with ExitStack() as stack:
        if zipfile.is_zipfile(input_path):
            archive = stack.enter_context(zipfile.ZipFile(input_path, "r"))
            manifest = load_manifest_from_archive(archive)
            temporary_directory = Path(
                stack.enter_context(tempfile.TemporaryDirectory(prefix="noop-to-csv-"))
            )
            database_path = extract_database(
                archive, temporary_directory / "noop-backup.sqlite"
            )
        else:
            database_path = input_path
            manifest = load_manifest_next_to_database(database_path)

        connection = connect_read_only(database_path)
        stack.callback(connection.close)
        validate_database(connection)
        written, flagged, stream_counts, missing_tables = write_csv(
            connection=connection,
            output_path=output_path,
            manifest=manifest,
            input_name=input_path.name,
            only_plausible=args.only_plausible,
            force=args.force,
        )

    print(f"Wrote {written:,} rows to {output_path}")
    if args.only_plausible:
        print(f"Skipped {flagged:,} rows with implausible or invalid timestamps.")
    else:
        print(
            f"Flagged {flagged:,} rows with implausible or invalid timestamps (kept)."
        )
    if stream_counts:
        counts = ", ".join(
            f"{stream}={count:,}" for stream, count in sorted(stream_counts.items())
        )
        print(f"Streams: {counts}")
    if missing_tables:
        print("Absent/empty-schema streams: " + ", ".join(missing_tables))
    print(
        "Binary waveform/raw-batch blobs and app-level summary tables are not "
        "flattened into this sensor CSV."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a NOOP .noopbak or extracted SQLite database to one CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run noop_to_csv.py backup.noopbak\n"
            "  uv run noop_to_csv.py backup.noopbak -o device-data.csv\n"
            "  uv run noop_to_csv.py backup.noopbak --only-plausible\n\n"
            "The default output is <input-name>-decoded.csv. Existing files are not "
            "replaced unless --force is used."
        ),
    )
    parser.add_argument("input", type=Path, help="NOOP .noopbak or SQLite file")
    parser.add_argument("-o", "--output", type=Path, help="destination CSV path")
    parser.add_argument(
        "--only-plausible",
        action="store_true",
        help="exclude timestamps outside NOOP's plausibility bounds",
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="replace an existing output file"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return convert(args)
    except (ConversionError, OSError, sqlite3.DatabaseError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
