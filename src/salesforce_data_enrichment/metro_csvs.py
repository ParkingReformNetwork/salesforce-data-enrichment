import csv
import os
from functools import cache
from io import StringIO
from pathlib import Path

from cryptography.fernet import Fernet

"""We encrypt the CSVs from https://ziptometro.com with a symmetric key to
avoid violating their terms of service."""


@cache
def _cipher() -> Fernet:
    return Fernet(os.environ.pop("ENCRYPTION_KEY"))


def parse_us_zip_to_metro(csv_text: str) -> dict[str, str]:
    return {
        row["Zip Code"]: row["Primary CBSA Name"]
        for row in csv.DictReader(StringIO(csv_text))
        if row["Primary CBSA Name"]
    }


def parse_us_city_and_state_to_metro(csv_text: str) -> dict[tuple[str, str], str]:
    return {
        (row["city"], row["state"]): row["metro"]
        for row in csv.DictReader(StringIO(csv_text))
    }


def read_us_zip_to_metro() -> dict[str, str]:
    encrypted_data = Path("data/us-zip-to-metro.encrypted.csv").read_bytes()
    return parse_us_zip_to_metro(_cipher().decrypt(encrypted_data).decode("utf-8"))


def read_us_city_and_state_to_metro() -> dict[tuple[str, str], str]:
    encrypted_data = Path("data/us-city-to-metro.encrypted.csv").read_bytes()
    return parse_us_city_and_state_to_metro(
        _cipher().decrypt(encrypted_data).decode("utf-8")
    )
