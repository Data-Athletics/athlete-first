from io import BytesIO

import pytest

from app.biometrics import decode_noop_csv
from app.biometrics.decoder import BiometricsCSVError
from tests.mock import EXPECTED_NOOP_DATA


def test_parse_noop_data():
    with open("tests/fixtures/noop_mock.csv", "rb") as file:
        result = decode_noop_csv(file)

        assert result == EXPECTED_NOOP_DATA


def test_parse_noop_data_rejects_missing_columns():
    with pytest.raises(BiometricsCSVError, match="missing required column"):
        decode_noop_csv(BytesIO(b"stream\nheart_rate\n"))


def test_parse_noop_data_rejects_unknown_streams():
    csv = b"stream,iso_utc\nunknown,2025-01-01T00:00:00Z\n"

    with pytest.raises(BiometricsCSVError, match="recognized biometric"):
        decode_noop_csv(BytesIO(csv))
