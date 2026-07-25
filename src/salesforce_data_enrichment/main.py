import logging
import sys
from argparse import ArgumentParser

from geopy import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from salesforce_data_enrichment import metro_csvs, salesforce_api, us_zip_lookup
from salesforce_data_enrichment.enrich import enrich_entry
from salesforce_data_enrichment.env import check_required_env_vars
from salesforce_data_enrichment.mailchimp_coordinates import get_coordinates_by_email

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
    check_required_env_vars()

    salesforce_client = salesforce_api.init_client()
    entries = salesforce_api.load_data(salesforce_client)
    logger.info(f"Loaded {len(entries)} Salesforce records")

    coordinates_by_email = get_coordinates_by_email()
    logger.info(f"Loaded {len(coordinates_by_email)} coordinates from Mailchimp")

    us_zip_to_metro = metro_csvs.read_us_zip_to_metro()
    us_city_and_state_to_metro = metro_csvs.read_us_city_and_state_to_metro()
    us_zip_to_city_state = us_zip_lookup.read_us_zip_to_city_state()
    geocoder = Nominatim(
        user_agent="parking_reform_network_data_enrichment", timeout=10
    )
    reverse_geocode = RateLimiter(
        geocoder.reverse, min_delay_seconds=1.1, swallow_exceptions=False
    )

    changed_records = 0
    failed_records = 0
    for entry in entries:
        original_model_dump = entry.model_dump(by_alias=True)

        try:
            enrich_entry(
                entry,
                coordinates_by_email.get(entry.email) if entry.email else None,
                reverse_geocode,
                us_zip_to_city_state,
                us_zip_to_metro,
                us_city_and_state_to_metro,
            )
        except Exception as e:
            failed_records += 1
            logger.warning(f"Failed to process {entry.uid}: {type(e).__name__}: {e}")
            continue

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

    logger.info(f"Total records changed: {changed_records}, failed: {failed_records}")
    if failed_records > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
