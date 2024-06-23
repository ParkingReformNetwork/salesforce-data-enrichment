import csv
from pathlib import Path

from geopy import Nominatim
from uszipcode import SearchEngine

import metro_csvs
from mailchimp_entry import MailchimpEntry
from salesforce_api import init_salesforce_client, load_salesforce_data


def main() -> None:
    salesforce_client = init_salesforce_client()
    entries = load_salesforce_data(salesforce_client)

    # TODO: read in Mailchimp data
    mailchimp_by_email: dict[str, MailchimpEntry] = {}

    us_zip_to_metro = metro_csvs.read_us_zip_to_metro()
    us_city_and_state_to_metro = metro_csvs.read_us_city_and_state_to_metro()
    zipcode_search_engine = SearchEngine()
    geocoder = Nominatim(user_agent="parking_reform_network_data_enrichment")

    for entry in entries:
        # The order of operations matters.
        if entry.email:
            entry.populate_via_latitude_longitude(
                mailchimp_by_email.get(entry.email), geocoder
            )
        entry.normalize()
        entry.populate_via_zipcode(zipcode_search_engine)
        entry.populate_metro_area(us_zip_to_metro, us_city_and_state_to_metro)

    with Path("data/result.csv").open("w", newline="") as f:
        result = [entry.model_dump(by_alias=True) for entry in entries]
        writer = csv.DictWriter(f, fieldnames=result[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


if __name__ == "__main__":
    main()
