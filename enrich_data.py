import csv
from pathlib import Path
from typing import Any

from uszipcode import SearchEngine


def main() -> None:
    with Path("prn_contact_addresses.csv").open() as f:
        original_data = csv.DictReader(f)
        result = list(original_data)
    result = [process_row(row) for row in result]
    with Path("result.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=original_data.fieldnames, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(result)


def process_row(row: dict[str, Any]) -> dict[str, Any]:
    result = {**row}

    # Normalize country code.
    if result["MailingCountry"] in ("US", "United States"):
        result["MailingCountry"] = "USA"

    # Lowercase all-caps city names.
    if result["MailingCity"].isupper():
        result["MailingCity"] = result["MailingCity"].title()

    # Normalize US zip codes to be 5 digits.
    if result["MailingCountry"] == "USA" and len(result["MailingPostalCode"]) > 5:
        assert result["MailingPostalCode"][5] == "-"
        result["MailingPostalCode"] = result["MailingPostalCode"][:5]

    # If missing, look up City and State for US zip codes.
    if (
        result["MailingCountry"] == "USA"
        and result["MailingPostalCode"]
        and (not result["MailingState"] or not result["MailingCity"])
    ):
        zipcode_info = SearchEngine().by_zipcode(result["MailingPostalCode"])
        if not result["MailingState"]:
            result["MailingState"] = zipcode_info.state
        if not result["MailingCity"]:
            result["MailingCity"] = zipcode_info.major_city

    return result


if __name__ == "__main__":
    main()
