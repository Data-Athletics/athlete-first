import argparse
import csv
import math
import random
from dataclasses import dataclass
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


@dataclass(frozen=True)
class DailyProfile:
    """Small day-to-day differences used to keep generated signals correlated."""

    resting_hr_offset: float
    activity_level: float
    temperature_offset: float
    respiration_offset: float
    movement_level: float
    exercise_sessions: tuple[tuple[float, float, float], ...]


def utc_string(timestamp: datetime) -> str:
    return timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def filename_timestamp(timestamp: datetime) -> str:
    """Return an ISO-like UTC timestamp that is safe to use in a filename."""

    return utc_string(timestamp).replace(":", "-")


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


def _daily_profiles(rng: random.Random, days: int) -> list[DailyProfile]:
    profiles: list[DailyProfile] = []
    for _ in range(days + 1):
        exercise_sessions = tuple(
            (rng.uniform(6.5, 20.5), rng.uniform(0.35, 1.25), rng.uniform(12.0, 34.0))
            for _ in range(rng.choice((1, 2)))
        )
        profiles.append(
            DailyProfile(
                resting_hr_offset=rng.gauss(0, 3.5),
                activity_level=rng.uniform(0.7, 1.35),
                temperature_offset=rng.gauss(0, 2.5),
                respiration_offset=rng.gauss(0, 0.8),
                movement_level=rng.uniform(0.7, 1.4),
                exercise_sessions=exercise_sessions,
            )
        )
    return profiles


def _profile_for(
    timestamp: datetime, start: datetime, profiles: list[DailyProfile]
) -> DailyProfile:
    day_index = (timestamp.date() - start.date()).days
    return profiles[min(max(day_index, 0), len(profiles) - 1)]


def _activity_load(minutes: int, profile: DailyProfile) -> float:
    daylight = max(0.0, math.sin((minutes - 360) / 1440 * math.pi * 2))
    exercise = sum(
        amplitude * math.exp(-0.5 * ((minutes / 60 - center) / duration) ** 2)
        for center, duration, amplitude in profile.exercise_sessions
    )
    return profile.activity_level * 1.2 * daylight + exercise


def _heart_rate_target(
    timestamp: datetime, start: datetime, profiles: list[DailyProfile]
) -> float:
    minutes = timestamp.hour * 60 + timestamp.minute
    profile = _profile_for(timestamp, start, profiles)
    activity = _activity_load(minutes, profile)
    circadian = 1.8 * math.sin((minutes - 240) / 1440 * math.pi * 2)
    return 58 + profile.resting_hr_offset + circadian + 5 * activity


def generate_rows(
    days: int,
    end: datetime,
    seed: int,
    sample_seconds: int = 60,
    rr_sample_seconds: int = 10,
) -> list[dict[str, object]]:
    rng = random.Random(seed)
    start = end - timedelta(days=days)
    profiles = _daily_profiles(rng, days)
    rows: list[dict[str, object]] = []
    timestamp = start
    sequence = 0
    heart_rate_drift = 0.0

    while timestamp <= end:
        minutes = timestamp.hour * 60 + timestamp.minute
        profile = _profile_for(timestamp, start, profiles)
        activity = _activity_load(minutes, profile)
        heart_rate_drift = 0.82 * heart_rate_drift + rng.gauss(0, 1.7)
        bpm = round(
            _heart_rate_target(timestamp, start, profiles)
            + heart_rate_drift
            + rng.gauss(0, 2.2)
        )

        if rng.random() < 0.002:
            bpm = rng.choice([38, 42, 155, 175, 195])

        bpm = max(35, min(210, bpm))
        heart_rate = base_row(timestamp, "heart_rate", "hrSample")
        heart_rate["hr_bpm"] = bpm
        rows.append(heart_rate)

        elapsed_seconds = (timestamp - start).total_seconds()
        skin_temp = round(
            1405
            + (timestamp.date() - start.date()).days * 0.8
            + profile.temperature_offset
            + 8 * math.sin((minutes - 240) / 1440 * math.pi * 2)
            + 1.5 * activity
            + rng.gauss(0, 3.5)
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
        respiration_rate = max(
            8.0, 12.0 + profile.respiration_offset + 1.8 * activity + rng.gauss(0, 0.35)
        )
        respiration_amplitude = 35 + min(activity, 6) * 18
        respiration["resp_raw"] = round(
            3070
            + respiration_amplitude
            * math.sin(elapsed_seconds / 60 * respiration_rate * math.pi * 2 / 60)
            + rng.gauss(0, 8)
        )
        rows.append(respiration)

        gravity = base_row(timestamp, "gravity", "gravitySample")
        movement = profile.movement_level * (0.25 + min(activity, 5) / 5)
        gravity.update(
            {
                "gravity_x": round(
                    0.07
                    + 0.025 * math.sin(elapsed_seconds / 900)
                    + rng.gauss(0, 0.008 + movement * 0.004),
                    9,
                ),
                "gravity_y": round(
                    0.67
                    + 0.035 * math.sin(elapsed_seconds / 1_300 + 1.2)
                    + rng.gauss(0, 0.008 + movement * 0.004),
                    9,
                ),
                "gravity_z": round(
                    0.74
                    + 0.03 * math.cos(elapsed_seconds / 1_100)
                    + rng.gauss(0, 0.008 + movement * 0.004),
                    9,
                ),
                "gravity_vector_magnitude_g": round(
                    max(0.92, rng.gauss(1.0, 0.004 + movement * 0.003)), 6
                ),
                "gravity_dynamic_accel_g": round(
                    abs(rng.gauss(0.012 + 0.025 * movement, 0.006 + 0.008 * movement)),
                    6,
                ),
            }
        )
        rows.append(gravity)

        optical = base_row(timestamp, "optical_raw", "spo2Sample")
        perfusion = max(0.0, 1.0 - min(activity, 5) * 0.04)
        optical.update(
            {
                "spo2_red_raw": round(
                    665
                    + 5 * perfusion * math.sin(elapsed_seconds / 180)
                    + rng.gauss(0, 10)
                ),
                "spo2_ir_raw": round(
                    725
                    + 7 * perfusion * math.cos(elapsed_seconds / 210)
                    + rng.gauss(0, 11)
                ),
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
        rr_minutes = rr_timestamp.hour * 60 + rr_timestamp.minute
        rr_profile = _profile_for(rr_timestamp, start, profiles)
        rr_activity = _activity_load(rr_minutes, rr_profile)
        target_bpm = max(
            40.0, _heart_rate_target(rr_timestamp, start, profiles) + rng.gauss(0, 1.5)
        )
        breathing_phase = rr_sequence / 8 * math.pi * 2
        rr_ms = round(
            60000 / target_bpm
            + 28 * math.sin(breathing_phase)
            + rng.gauss(0, 28 + min(rr_activity, 5) * 3)
        )
        rr_ms = max(450, min(1_800, rr_ms))
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
        profile = _profile_for(timestamp, start, profiles)
        skin_temp = round(
            1405 + day * 0.8 + profile.temperature_offset + rng.gauss(0, 4)
        )
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
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--output", type=Path, help="Exact output CSV path; overrides --output-dir"
    )
    output_group.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home(),
        help="Directory for the timestamped CSV filename (default: home directory)",
    )
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--sample-seconds", type=int, default=60)
    parser.add_argument("--rr-sample-seconds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261028)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc)
    end = generated_at
    if args.days <= 0 or args.sample_seconds <= 0 or args.rr_sample_seconds <= 0:
        parser.error(
            "--days, --sample-seconds, and --rr-sample-seconds must be positive"
        )

    rows = generate_rows(
        args.days, end, args.seed, args.sample_seconds, args.rr_sample_seconds
    )
    output_path = args.output or (
        args.output_dir / f"biometrics_one_month_{filename_timestamp(generated_at)}.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows):,} rows at {output_path}")
    print(f"Range: {utc_string(end - timedelta(days=args.days))} to {utc_string(end)}")


if __name__ == "__main__":
    main()
