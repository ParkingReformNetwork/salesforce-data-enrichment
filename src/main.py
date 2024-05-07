import csv
from pathlib import Path
from typing import Any

from geopy import Nominatim
from uszipcode import SearchEngine

from salesforce_entry import SalesforceEntry
from hardcoded_addresses import ADDRESS_STRINGS
from state_codes import US_STATES_TO_CODES


def main() -> None:
    with Path("data/salesforce.csv").open() as f:
        raw_original_data = csv.DictReader(f)
        entries = [SalesforceEntry(**row) for row in raw_original_data]
    with Path("data/mailchimp.csv").open() as f:
        mailchimp_by_email = {
            row["Email Address"]: {**row} for row in csv.DictReader(f)
        }
    with Path("data/us-zip-to-metro.csv").open() as f:
        us_zip_to_metro_name = {
            row["Zip Code"]: row["Primary CBSA Name"]
            for row in csv.DictReader(f)
            if row["Primary CBSA Name"]
        }

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
        writer = csv.DictWriter(
            f,
            fieldnames=[*raw_original_data.fieldnames, "MetropolitanArea"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows([entry.model_dump(by_alias=True) for entry in entries])


def process_salesforce_entry(
    entry: SalesforceEntry,
    zipcode_search_engine: SearchEngine,
    geocoder: Nominatim,
    mailchimp_by_email: dict[str, dict[str, Any]],
    us_zip_to_metro_name: dict[str, str],
) -> None:
    # Enrich Salesforce location data with Mailchimp data.
    if entry.email in mailchimp_by_email and (
        not entry.country or not entry.state or not entry.city or not entry.zip
    ):
        mailchimp_data = mailchimp_by_email[entry.email]

        # If there's an exact address, use that.
        if addr := mailchimp_data["Address"]:
            mailchimp_addr = ADDRESS_STRINGS[addr]
            if not entry.country:
                entry.country = mailchimp_addr.country
            if not entry.state:
                entry.state = mailchimp_addr.state
            if not entry.city:
                entry.city = mailchimp_addr.city
            if not entry.zip:
                entry.zip = mailchimp_addr.postal
            if not entry.street:
                entry.street = mailchimp_addr.street

        # Next, reverse geocode the lat/long. This allows us to get a zip code.
        elif (lat := mailchimp_data["LATITUDE"]) and (
            long := mailchimp_data["LONGITUDE"]
        ):
            long = long.lstrip("'")
            entry.latitude = lat
            entry.longitude = long

            addr = geocoder.reverse(f"{lat}, {long}").raw["address"]
            if not entry.country:
                entry.country = addr.get("country_code", "").upper()
            if not entry.state:
                entry.state = addr.get("state", "")
            if not entry.city:
                entry.city = addr.get("city", "")
            if not entry.zip:
                entry.zip = addr.get("postcode", "")

        # Finally, see if the city, state/province, country was set. This data comes from us, not
        # the IP address.
        elif (
            city_str_split := mailchimp_data["City, State/Province, Country"].split(",")
        ) and len(city_str_split) == 3:
            city, state, country = city_str_split
            if not entry.country:
                entry.country = country.strip()
            if not entry.state:
                entry.state = state.strip()
            if not entry.city:
                entry.city = city.strip()

    # Normalize country code.
    if entry.country in ("US", "United States"):
        entry.country = "USA"

    # Convert US state names to two-digit codes.
    if entry.country == "USA" and len(entry.state) > 2:
        entry.state = US_STATES_TO_CODES[entry.state]

    # Lowercase all-caps city names.
    if entry.city.isupper():
        entry.city = entry.city.title()

    # Normalize US zip codes to be 5 digits.
    if entry.country == "USA" and len(entry.zip) > 5:
        assert entry.zip[5] == "-"
        entry.zip = entry.zip[:5]

    # If missing, look up City and State for US zip codes.
    if entry.country == "USA" and entry.zip and (not entry.state or not entry.city):
        zipcode_info = zipcode_search_engine.by_zipcode(entry.zip)
        if not entry.state:
            entry.state = zipcode_info.state
        if not entry.city:
            entry.city = zipcode_info.major_city

    # Add metro area for US zip codes.
    entry.metro = (
        us_zip_to_metro_name.get(entry.zip, "")
        if entry.country == "USA" and entry.zip
        else ""
    )


if __name__ == "__main__":
    main()
