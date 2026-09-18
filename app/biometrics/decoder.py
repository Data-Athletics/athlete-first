from typing import Any, BinaryIO, cast

import pandas as pd

from app.biometrics.constants import (
    NOOP_DATA_MODELS,
    NOOP_DATA_ROWS,
    NOOP_SOURCE_COLUMN,
    NOOP_TIME_COLUMN,
)
from app.biometrics.types import NoopData


def decode_noop_csv(file: BinaryIO) -> NoopData:
    """Decodes csv file into data model for database insertion"""

    df = pd.read_csv(file)
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

        for record in records:
            result.add(source_type, model(**record))

    return result
