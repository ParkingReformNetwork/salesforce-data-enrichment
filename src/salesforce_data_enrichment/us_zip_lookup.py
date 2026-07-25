import csv
from pathlib import Path


def parse_us_zip_to_city_state(csv_text: str) -> dict[str, tuple[str, str]]:
    return {
        row["zip"]: (row["city"], row["state"])
        for row in csv.DictReader(csv_text.splitlines())
    }


def read_us_zip_to_city_state() -> dict[str, tuple[str, str]]:
    csv_text = Path("data/us-zip-to-city-state.csv").read_text()
    return parse_us_zip_to_city_state(csv_text)
