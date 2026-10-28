import argparse
import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

CSV_COLUMNS = [
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
    "spo2_red_raw",
    "spo2_ir_raw",
    "skin_temp_raw",
    "skin_temp_aux1_raw",
    "skin_temp_aux2_raw",
    "resp_raw",
    "battery_soc_pct",
    "battery_mv",
    "battery_charging",
    "event_kind",
    "event_payload_json",
    "synced",
]


def utc_string(timestamp: datetime) -> str:
    return timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def base_row(timestamp: datetime, stream: str, source_table: str) -> dict[str, object]:
    return {
        "device_id": "my-whoop",
        "unix_s": timestamp.timestamp(),
        "iso_utc": utc_string(timestamp),
        "timestamp_status": "plausible_by_noop_bounds",
        "stream": stream,
        "source_table": source_table,
        "synced": 0,
    }


def generate_rows(
    days: int,
    end: datetime,
    seed: int,
    sample_seconds: int = 60,
    rr_sample_seconds: int = 10,
) -> list[dict[str, object]]:
    rng = random.Random(seed)
    start = end - timedelta(days=days)
    rows: list[dict[str, object]] = []
    timestamp = start
    sequence = 0

    while timestamp <= end:
        minutes = timestamp.hour * 60 + timestamp.minute
        daily_activity = max(0.0, math.sin((minutes - 390) / 1440 * math.pi * 2))
        bpm = round(62 + 14 * daily_activity + rng.gauss(0, 3))

        if rng.random() < 0.002:
            bpm = rng.choice([38, 42, 155, 175, 195])

        bpm = max(35, min(210, bpm))
        heart_rate = base_row(timestamp, "heart_rate", "hrSample")
        heart_rate["hr_bpm"] = bpm
        rows.append(heart_rate)

        day_index = (timestamp.date() - start.date()).days
        skin_temp = round(
            1405
            + day_index * 0.8
            + 10 * math.sin(minutes / 1440 * math.pi * 2)
            + rng.gauss(0, 5)
        )
        if rng.random() < 0.001:
            skin_temp += rng.choice([-35, 35])
        skin_temperature = base_row(timestamp, "skin_temperature_raw", "skinTempSample")
        skin_temperature.update(
            {
                "skin_temp_raw": skin_temp,
                "skin_temp_aux1_raw": skin_temp - 2,
                "skin_temp_aux2_raw": skin_temp + 2,
            }
        )
        rows.append(skin_temperature)

        respiration = base_row(timestamp, "respiration_raw", "respSample")
        respiration["resp_raw"] = round(3070 + rng.gauss(0, 25))
        rows.append(respiration)

        gravity = base_row(timestamp, "gravity", "gravitySample")
        gravity.update(
            {
                "gravity_x": round(rng.gauss(0.07, 0.008), 9),
                "gravity_y": round(rng.gauss(0.67, 0.008), 9),
                "gravity_z": round(rng.gauss(0.74, 0.008), 9),
                "gravity_vector_magnitude_g": round(rng.gauss(1.0, 0.002), 6),
                "gravity_dynamic_accel_g": round(abs(rng.gauss(0.014, 0.004)), 6),
            }
        )
        rows.append(gravity)

        optical = base_row(timestamp, "optical_raw", "spo2Sample")
        optical.update(
            {
                "spo2_red_raw": round(665 + rng.gauss(0, 8)),
                "spo2_ir_raw": round(725 + rng.gauss(0, 8)),
            }
        )
        rows.append(optical)

        sequence += 1
        timestamp += timedelta(seconds=sample_seconds)

    # RR samples need a denser stream than the other generated metrics so the
    # respiratory-rate calculation can detect peaks in its five-minute window.
    rr_timestamp = start
    rr_sequence = 0
    while rr_timestamp <= end:
        breathing_phase = rr_sequence / 5 * math.pi * 2
        rr_ms = round(1_100 + 240 * math.sin(breathing_phase) + rng.gauss(0, 18))
        rr_ms = max(700, min(1_500, rr_ms))
        rr_interval = base_row(rr_timestamp, "rr_interval", "rrInterval")
        rr_interval.update(
            {
                "rr_ms": rr_ms,
                "rr_instant_bpm": round(60000 / rr_ms, 2),
                "rr_seq": rr_sequence,
                "rr_ord": 0,
                "rr_source_channel": 0,
                "rr_stored_ts_suspect": 0,
            }
        )
        rows.append(rr_interval)
        rr_sequence += 1
        rr_timestamp += timedelta(seconds=rr_sample_seconds)

    # The source data also contains a daily skin-temperature record outside
    # the synchronized sensor stream.
    daily_timestamp = start.replace(
        hour=end.hour, minute=end.minute, second=end.second, microsecond=0
    )
    for day in range(days):
        timestamp = daily_timestamp + timedelta(days=day)
        if timestamp > end:
            break
        skin_temp = round(1405 + day * 0.8) + rng.randint(-3, 3)
        skin_temperature = base_row(timestamp, "skin_temperature_raw", "skinTempSample")
        skin_temperature.update(
            {
                "skin_temp_raw": skin_temp,
                "skin_temp_aux1_raw": skin_temp - 2,
                "skin_temp_aux2_raw": skin_temp + 2,
            }
        )
        rows.append(skin_temperature)

    # Battery and event rows mirror the converter output and make the file
    # useful for exercising non-sensor records as well.
    battery_timestamp = start
    while battery_timestamp <= end:
        if battery_timestamp == start or rng.random() < 1 / 7:
            soc = round(
                35
                + 55
                * (battery_timestamp - start).total_seconds()
                / max((end - start).total_seconds(), 1)
            )
            soc = max(10, min(95, soc + rng.randint(-3, 3)))
            battery_mv = round(3700 + soc * 5 + rng.gauss(0, 15))
            battery = base_row(battery_timestamp, "battery", "battery")
            battery.update(
                {
                    "battery_soc_pct": soc,
                    "battery_mv": battery_mv,
                    "battery_charging": int(soc < 45),
                }
            )
            rows.append(battery)

            event = base_row(battery_timestamp, "event", "event")
            event.update(
                {
                    "event_kind": "BATTERY",
                    "event_payload_json": f'{{"BATTERY": {{"soc": {soc}, "mv": {battery_mv}}}}}',
                }
            )
            rows.append(event)
        battery_timestamp += timedelta(days=1)

    rows.sort(key=lambda row: (row["unix_s"], row["stream"]))

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "biometrics_one_month.csv",
        help="Output CSV path",
    )
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--sample-seconds", type=int, default=60)
    parser.add_argument("--rr-sample-seconds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261028)
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    if args.days <= 0 or args.sample_seconds <= 0 or args.rr_sample_seconds <= 0:
        parser.error(
            "--days, --sample-seconds, and --rr-sample-seconds must be positive"
        )

    rows = generate_rows(
        args.days, end, args.seed, args.sample_seconds, args.rr_sample_seconds
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows):,} rows at {args.output}")
    print(f"Range: {utc_string(end - timedelta(days=args.days))} to {utc_string(end)}")


if __name__ == "__main__":
    main()
