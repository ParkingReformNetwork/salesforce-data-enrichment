import csv
from pathlib import Path

from geopy import Nominatim
from uszipcode import SearchEngine

from zip_to_metro import read_us_zip_to_metro
from mailchimp_entry import MailchimpEntry
from salesforce_entry import SalesforceEntry


def main() -> None:
    with Path("data/salesforce.csv").open() as f:
        entries = [SalesforceEntry(**row) for row in csv.DictReader(f)]
    with Path("data/mailchimp.csv").open() as f:
        mailchimp_by_email = {
            row["Email Address"]: MailchimpEntry(**row) for row in csv.DictReader(f)
        }

    us_zip_to_metro_name = read_us_zip_to_metro()
    zipcode_search_engine = SearchEngine()
    geocoder = Nominatim(user_agent="parking_reform_network_data_enrichment")

    for entry in entries:
        # The order of operations matters.
        entry.populate_via_mailchimp(mailchimp_by_email.get(entry.email), geocoder)
        entry.normalize()
        entry.populate_city_via_zipcode(zipcode_search_engine)
        entry.populate_metro_area(us_zip_to_metro_name)

    with Path("data/result.csv").open("w", newline="") as f:
        result = [entry.model_dump(by_alias=True) for entry in entries]
        writer = csv.DictWriter(f, fieldnames=result[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


if __name__ == "__main__":
    main()
