import csv
from pathlib import Path
from typing import Any

from uszipcode import SearchEngine

from hardcoded_addresses import ADDRESS_STRINGS


def main() -> None:
    with Path("prn_contact_addresses.csv").open() as f:
        original_data = csv.DictReader(f)
        result = list(original_data)
    with Path("subscribed_members_export.csv").open() as f:
        raw_subscribed_members_data = csv.DictReader(f)
        subscribed_members_by_email = {
            row["Email Address"]: {**row} for row in raw_subscribed_members_data
        }

    result = [process_row(row, subscribed_members_by_email) for row in result]
    with Path("result.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=original_data.fieldnames, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(result)


def process_row(
    row: dict[str, Any], subscribed_members_by_email: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    result = {**row}

    # Enrich Salesforce data with Mailchimp data.
    if (email := row["Email"]) in subscribed_members_by_email:
        mailchimp_data = subscribed_members_by_email[email]
        if mailchimp_data["Address"]:
            mailchimp_addr = ADDRESS_STRINGS[mailchimp_data["Address"]]
            if not result["MailingCountry"]:
                result["MailingCountry"] = mailchimp_addr.country
            if not result["MailingState"]:
                result["MailingState"] = mailchimp_addr.state
            if not result["MailingCity"]:
                result["MailingCity"] = mailchimp_addr.city
            if not result["MailingPostalCode"]:
                result["MailingPostalCode"] = mailchimp_addr.postal
            if not result["MailingStreet"]:
                result["MailingStreet"] = mailchimp_addr.street

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
