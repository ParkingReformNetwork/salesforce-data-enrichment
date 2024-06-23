import logging
from argparse import ArgumentParser

from geopy import Nominatim
from uszipcode import SearchEngine

import metro_csvs
import salesforce_api
from mailchimp_entry import MailchimpEntry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="Write results to Salesforce"
    )
    return parser


def main() -> None:
    args = create_parser().parse_args()

    salesforce_client = salesforce_api.init_client()
    entries = salesforce_api.load_data(salesforce_client)

    # TODO: read in Mailchimp data
    mailchimp_by_email: dict[str, MailchimpEntry] = {}

    us_zip_to_metro = metro_csvs.read_us_zip_to_metro()
    us_city_and_state_to_metro = metro_csvs.read_us_city_and_state_to_metro()
    zipcode_search_engine = SearchEngine()
    geocoder = Nominatim(user_agent="parking_reform_network_data_enrichment")

    uid_to_changes: dict[str, dict[str, str]] = {}
    for entry in entries:
        original_model_dump = entry.model_dump(by_alias=True)

        # The order of operations matters.
        if entry.email:
            entry.populate_via_latitude_longitude(
                mailchimp_by_email.get(entry.email), geocoder
            )
        entry.normalize()
        entry.populate_via_zipcode(zipcode_search_engine)
        entry.populate_metro_area(us_zip_to_metro, us_city_and_state_to_metro)

        changes = entry.compute_changes(original_model_dump)
        if changes:
            logger.info(f"Changes made to {entry.uid}: {sorted(changes.keys())}")
            uid_to_changes[entry.uid] = changes

    logger.info(f"Total changes made: {len(uid_to_changes)}")

    if args.write:
        salesforce_api.write_changes(salesforce_client, uid_to_changes)
        logger.info(f"Updated Salesforce records ({len(uid_to_changes)} records)")
    else:
        logger.warning("Results not written to Salesforce.")


if __name__ == "__main__":
    main()
