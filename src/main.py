import csv
from pathlib import Path
from typing import Any

from geopy import Nominatim
from uszipcode import SearchEngine

from mailchimp_entry import MailchimpEntry
from salesforce_entry import SalesforceEntry
from hardcoded_addresses import ADDRESS_STRINGS


def main() -> None:
    with Path("data/salesforce.csv").open() as f:
        entries = [SalesforceEntry(**row) for row in csv.DictReader(f)]
    with Path("data/mailchimp.csv").open() as f:
        mailchimp_by_email = {
            row["Email Address"]: MailchimpEntry(**row) for row in csv.DictReader(f)
        }

    us_zip_to_metro_name = read_us_zip_to_metro("data/us-zip-to-metro.csv")
    zipcode_search_engine = SearchEngine()
    geocoder = Nominatim(user_agent="parking_reform_network_data_enrichment")
    for entry in entries:
        process_salesforce_entry(
            entry,
            zipcode_search_engine,
            geocoder,
            mailchimp_by_email,
            us_zip_to_metro_name,
        )

    with Path("data/result.csv").open("w", newline="") as f:
        result = [entry.model_dump(by_alias=True) for entry in entries]
        writer = csv.DictWriter(f, fieldnames=result[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


def process_salesforce_entry(
    entry: SalesforceEntry,
    zipcode_search_engine: SearchEngine,
    geocoder: Nominatim,
    mailchimp_by_email: dict[str, MailchimpEntry],
    us_zip_to_metro_name: dict[str, str],
) -> None:
    # Enrich Salesforce location data with Mailchimp data.
    if entry.email in mailchimp_by_email and (
        not entry.country or not entry.state or not entry.city or not entry.zipcode
    ):
        mailchimp_entry = mailchimp_by_email[entry.email]

        # If there's an exact address, use that.
        if mailchimp_entry.address:
            addr = ADDRESS_STRINGS[mailchimp_entry.address]
            entry.country = addr.country
            entry.state = addr.state
            entry.city = addr.city
            entry.zipcode = addr.postal
            entry.street = addr.street

        # Next, reverse geocode the lat/long. This allows us to get a zip code.
        elif mailchimp_entry.latitude and mailchimp_entry.longitude:
            entry.latitude = mailchimp_entry.latitude
            entry.longitude = mailchimp_entry.longitude

            addr = geocoder.reverse(
                f"{mailchimp_entry.latitude}, {mailchimp_entry.longitude}"
            ).raw["address"]
            if not entry.country:
                entry.country = addr.get("country_code", "").upper()
            if not entry.state:
                entry.state = addr.get("state", "")
            if not entry.city:
                entry.city = addr.get("city", "")
            if not entry.zipcode:
                entry.zipcode = addr.get("postcode", "")

        # Finally, see if the city, state/province, country was set. This data comes from us, not
        # the IP address.
        elif mailchimp_entry.city_state_country:
            entry.city, entry.state, entry.country = mailchimp_entry.city_state_country

    entry.normalize()
    entry.populate_city_via_zipcode(zipcode_search_engine)
    entry.populate_metro_area(us_zip_to_metro_name)


def read_us_zip_to_metro(fp: str) -> dict[str, str]:
    with Path(fp).open() as f:
        return {
            row["Zip Code"]: row["Primary CBSA Name"]
            for row in csv.DictReader(f)
            if row["Primary CBSA Name"]
        }


if __name__ == "__main__":
    main()
