import csv
import os
from io import StringIO
from pathlib import Path

from cryptography.fernet import Fernet


def read_us_zip_to_metro() -> dict[str, str]:
    key = os.environ.pop("ENCRYPTION_KEY")
    cipher = Fernet(key)

    encrypted_data = Path("us-zip-to-metro.encrypted.csv").read_bytes()
    data = cipher.decrypt(encrypted_data).decode("utf-8")
    return {
        row["Zip Code"]: row["Primary CBSA Name"]
        for row in csv.DictReader(StringIO(data))
        if row["Primary CBSA Name"]
    }
