import csv
from pathlib import Path
from typing import Any

def main() -> None:
    with Path("prn_contact_addresses.csv").open() as f:
        original_data = csv.DictReader(f)
        result = list(original_data)
    result = [process_row(row) for row in result]
    with Path("result.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=original_data.fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


def process_row(row: dict[str, Any]) -> dict[str, Any]:
    result = {**row}
    if result["MailingCountry"] == "US":
        result["MailingCountry"] = "USA"
    return result



if __name__ == '__main__':
    main()
