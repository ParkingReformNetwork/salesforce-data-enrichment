import csv
from pathlib import Path
from typing import Any

def main() -> None:
    with Path("prn_contact_addresses.csv").open() as f:
        original_data = csv.DictReader(f)
        result = list(original_data)
    result = normalize_country_code(result)
    with Path("result.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=original_data.fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)

def normalize_country_code(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return data


if __name__ == '__main__':
    main()
