from typing import Any, BinaryIO, cast

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from pydantic import ValidationError

from app.biometrics.constants import (
    NOOP_DATA_MODELS,
    NOOP_DATA_ROWS,
    NOOP_SOURCE_COLUMN,
    NOOP_TIME_COLUMN,
)
from app.biometrics.types import NoopData


class BiometricsCSVError(ValueError):
    """Raised when an uploaded biometrics CSV cannot be validated."""


def decode_noop_csv(file: BinaryIO) -> NoopData:
    """Decodes csv file into data model for database insertion"""

    try:
        df = pd.read_csv(file)
    except (EmptyDataError, ParserError, UnicodeDecodeError) as exc:
        raise BiometricsCSVError(
            "CSV could not be read. Upload a valid UTF-8 biometrics CSV."
        ) from exc

    required_columns = {NOOP_SOURCE_COLUMN, NOOP_TIME_COLUMN}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise BiometricsCSVError(f"CSV is missing required column(s): {missing}.")

    recognized_streams = set(df[NOOP_SOURCE_COLUMN].dropna()).intersection(
        NOOP_DATA_ROWS
    )
    if not recognized_streams:
        raise BiometricsCSVError(
            "CSV does not contain any recognized biometric data streams."
        )

    for source_type in recognized_streams:
        missing_columns = set(NOOP_DATA_ROWS[source_type]).difference(df.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise BiometricsCSVError(
                f"CSV is missing columns for {source_type}: {missing}."
            )

    result: NoopData = NoopData()

    for source_type, cols in NOOP_DATA_ROWS.items():
        # Check row by source stream type and grab specified columns with timestamp for that record
        records = (
            df.loc[df[NOOP_SOURCE_COLUMN] == source_type, [*cols, NOOP_TIME_COLUMN]]
            .dropna(how="all")
            .rename(columns={NOOP_TIME_COLUMN: "timestamp"})
            .to_dict(orient="records")
        )
        records = cast(list[dict[str, Any]], records)

        # Get model for source stream type
        model = NOOP_DATA_MODELS[source_type]

        for row_number, record in enumerate(records, start=2):
            try:
                result.add(source_type, model(**record))
            except ValidationError as exc:
                raise BiometricsCSVError(
                    f"Invalid {source_type} data near CSV row {row_number}."
                ) from exc

    if not any(
        (
            result.heart_rate,
            result.rr_interval,
            result.gravity,
            result.optical_raw,
            result.skin_temperature_raw,
            result.respiration_raw,
        )
    ):
        raise BiometricsCSVError("CSV does not contain any usable biometric rows.")

    return result
