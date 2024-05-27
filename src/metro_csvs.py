import csv
import os
from io import StringIO
from pathlib import Path

from cryptography.fernet import Fernet

"""We encrypt the CSVs from https://ziptometro.com with a symmetric key to
avoid violating their terms of service."""

_KEY = os.environ.pop("ENCRYPTION_KEY")
CIPHER = Fernet(_KEY)


def read_us_zip_to_metro() -> dict[str, str]:
    encrypted_data = Path("data/us-zip-to-metro.encrypted.csv").read_bytes()
    data = CIPHER.decrypt(encrypted_data).decode("utf-8")
    return {
        row["Zip Code"]: row["Primary CBSA Name"]
        for row in csv.DictReader(StringIO(data))
        if row["Primary CBSA Name"]
    }


def read_us_city_and_state_to_metro() -> dict[tuple[str, str], str]:
    encrypted_data = Path("data/us-city-to-metro.encrypted.csv").read_bytes()
    data = CIPHER.decrypt(encrypted_data).decode("utf-8")
    return {
        (row["city"], row["state"]): row["metro"]
        for row in csv.DictReader(StringIO(data))
    }
