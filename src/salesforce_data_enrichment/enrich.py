from salesforce_data_enrichment.mailchimp_coordinates import Coordinates
from salesforce_data_enrichment.salesforce_entry import ReverseGeocode, SalesforceEntry


def enrich_entry(
    entry: SalesforceEntry,
    coordinates: Coordinates | None,
    reverse_geocode: ReverseGeocode,
    us_zip_to_city_state: dict[str, tuple[str, str]],
    us_zip_to_metro: dict[str, str],
    us_city_and_state_to_metro: dict[tuple[str, str], str],
) -> None:
    """Fill in missing location data on the entry, in place.

    The order of operations matters. Reverse geocoding runs first because it can supply a
    zip code, which the later steps need; normalize() then puts the country and state into
    the form those lookups expect.
    """
    entry.populate_via_coordinates(coordinates, reverse_geocode)
    entry.normalize()
    entry.populate_via_us_zipcode(us_zip_to_city_state)
    entry.populate_us_metro_area(us_zip_to_metro, us_city_and_state_to_metro)
