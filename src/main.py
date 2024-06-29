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

    changed_records = 0
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
        if not changes:
            continue

        changed_records += 1
        changed_keys = sorted(changes.keys())
        if args.write:
            salesforce_api.write_change(salesforce_client, entry.uid, changes)
            logger.info(f"Changes saved to Salesforce for {entry.uid}: {changed_keys}")
        else:
            logger.info(
                f"Changes computed (but not written) for {entry.uid}: {changed_keys}"
            )

    logger.info(f"Total records changed: {changed_records}")


if __name__ == "__main__":
    main()
