from app.biometrics import decode_noop_csv
from tests.biometrics import EXPECTED_NOOP_DATA


def test_parse_noop_data():
    with open("tests/fixtures/noop_mock.csv", "rb") as file:
        result = decode_noop_csv(file)

        assert result == EXPECTED_NOOP_DATA
