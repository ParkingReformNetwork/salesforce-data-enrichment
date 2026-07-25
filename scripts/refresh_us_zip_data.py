"""Refresh data/us-zip-to-city-state.csv from GeoNames' public postal code dataset.

Source: https://download.geonames.org/export/zip/US.zip (CC BY 4.0, geonames.org).
Run with: uv run python scripts/refresh_us_zip_data.py
"""

import csv
import io
import urllib.request
import zipfile
from pathlib import Path

GEONAMES_URL = "https://download.geonames.org/export/zip/US.zip"
OUTPUT_PATH = Path("data/us-zip-to-city-state.csv")


def fetch_us_txt() -> str:
    with urllib.request.urlopen(GEONAMES_URL) as response:
        archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        return archive.read("US.txt").decode("utf-8")


def parse_zip_to_city_state(us_txt: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    reader = csv.reader(io.StringIO(us_txt), delimiter="\t")
    for row in reader:
        _country_code, zipcode, city, _state_name, state_code = row[:5]
        # A handful of zip codes (e.g. military ones) have multiple rows; keep
        # the first one we see.
        if zipcode not in result:
            result[zipcode] = (city, state_code)
    return result


def write_csv(zip_to_city_state: dict[str, tuple[str, str]]) -> None:
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["zip", "city", "state"])
        for zipcode, (city, state) in sorted(zip_to_city_state.items()):
            writer.writerow([zipcode, city, state])


def main() -> None:
    us_txt = fetch_us_txt()
    zip_to_city_state = parse_zip_to_city_state(us_txt)
    write_csv(zip_to_city_state)
    print(f"Wrote {len(zip_to_city_state)} zip codes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
