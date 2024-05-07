import csv
from pathlib import Path
from typing import Any

from geopy import Nominatim
from uszipcode import SearchEngine

from hardcoded_addresses import ADDRESS_STRINGS
from state_codes import US_STATES_TO_CODES


def main() -> None:
    with Path("data/salesforce.csv").open() as f:
        raw_original_data = csv.DictReader(f)
        original_data = list(raw_original_data)
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
    result = [
        process_row(
            row,
            zipcode_search_engine,
            geocoder,
            mailchimp_by_email,
            us_zip_to_metro_name,
        )
        for row in original_data
    ]
    with Path("data/result.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[*raw_original_data.fieldnames, "MetropolitanArea"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(result)


def process_row(
    row: dict[str, Any],
    zipcode_search_engine: SearchEngine,
    geocoder: Nominatim,
    mailchimp_by_email: dict[str, dict[str, Any]],
    us_zip_to_metro_name: dict[str, str],
) -> dict[str, Any]:
    result = {**row}

    # Enrich Salesforce location data with Mailchimp data.
    if (email := row["Email"]) in mailchimp_by_email and (
        not result["MailingCountry"]
        or not result["MailingState"]
        or not result["MailingCity"]
        or not result["MailingPostalCode"]
    ):
        mailchimp_data = mailchimp_by_email[email]

        # If there's an exact address, use that.
        if addr := mailchimp_data["Address"]:
            mailchimp_addr = ADDRESS_STRINGS[addr]
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

        # Next, reverse geocode the lat/long. This allows us to get a zip code.
        elif (lat := mailchimp_data["LATITUDE"]) and (
            long := mailchimp_data["LONGITUDE"]
        ):
            result["MailingLatitude"] = mailchimp_data["LATITUDE"]
            result["MailingLongitude"] = mailchimp_data["LONGITUDE"]
            long = long.lstrip("'")
            addr = geocoder.reverse(f"{lat}, {long}").raw["address"]
            if not result["MailingCountry"]:
                result["MailingCountry"] = addr.get("country_code", "").upper()
            if not result["MailingState"]:
                result["MailingState"] = addr.get("state", "")
            if not result["MailingCity"]:
                result["MailingCity"] = addr.get("city", "")
            if not result["MailingPostalCode"]:
                result["MailingPostalCode"] = addr.get("postcode", "")

        # Finally, see if the city, state/province, country was set. This data comes from us, not
        # the IP address.
        elif (
            city_str_split := mailchimp_data["City, State/Province, Country"].split(",")
        ) and len(city_str_split) == 3:
            city, state, country = city_str_split
            if not result["MailingCountry"]:
                result["MailingCountry"] = country.strip()
            if not result["MailingState"]:
                result["MailingState"] = state.strip()
            if not result["MailingCity"]:
                result["MailingCity"] = city.strip()

    # Normalize country code.
    if result["MailingCountry"] in ("US", "United States"):
        result["MailingCountry"] = "USA"

    # Convert US state names to two-digit codes.
    if result["MailingCountry"] == "USA" and len(result["MailingState"]) > 2:
        result["MailingState"] = US_STATES_TO_CODES[result["MailingState"]]

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
        zipcode_info = zipcode_search_engine.by_zipcode(result["MailingPostalCode"])
        if not result["MailingState"]:
            result["MailingState"] = zipcode_info.state
        if not result["MailingCity"]:
            result["MailingCity"] = zipcode_info.major_city

    # Add metro area for US zip codes.
    result["MetropolitanArea"] = (
        us_zip_to_metro_name.get(result["MailingPostalCode"], "")
        if result["MailingCountry"] == "USA" and result["MailingPostalCode"]
        else ""
    )
    return result


if __name__ == "__main__":
    main()
