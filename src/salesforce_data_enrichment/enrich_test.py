"""Tests for the order of operations in the enrichment pipeline."""

from unittest.mock import Mock

from testing_helpers import build_entry, build_geocode

from salesforce_data_enrichment.enrich import enrich_entry
from salesforce_data_enrichment.mailchimp_coordinates import Coordinates
from salesforce_data_enrichment.salesforce_entry import SalesforceEntry

COORDINATES = Coordinates(latitude=1.1, longitude=4.2)

US_ZIP_TO_CITY_STATE = {"11370": ("East Elmhurst", "NY")}
US_ZIP_TO_METRO = {"11370": "New York-Newark-Jersey City"}
US_CITY_AND_STATE_TO_METRO = {("Tempe", "AZ"): "Phoenix-Mesa-Chandler"}


def enrich(
    entry: SalesforceEntry,
    coordinates: Coordinates | None,
    reverse_geocode: Mock | None = None,
) -> None:
    enrich_entry(
        entry,
        coordinates,
        reverse_geocode if reverse_geocode is not None else build_geocode(),
        US_ZIP_TO_CITY_STATE,
        US_ZIP_TO_METRO,
        US_CITY_AND_STATE_TO_METRO,
    )


def test_normalizes_geocoded_country_and_state() -> None:
    """Nominatim returns "us" and "New York"; Salesforce wants "USA" and "NY"."""
    entry = build_entry()
    enrich(entry, coordinates=COORDINATES)
    assert entry.country == "USA"
    assert entry.state == "NY"
    assert entry.city == "New York"


def test_metro_is_derived_from_the_geocoded_zip() -> None:
    """The metro lookup depends on a zip that only geocoding could supply."""
    entry = build_entry()
    enrich(entry, coordinates=COORDINATES)
    assert entry.zipcode == "11370"
    assert entry.metro == "New York-Newark-Jersey City"


def test_metro_lookup_uses_the_normalized_zip() -> None:
    """A zip+4 must be shortened to 5 digits before the metro lookup, not after."""
    entry = build_entry()
    enrich(
        entry,
        coordinates=COORDINATES,
        reverse_geocode=build_geocode(
            {"country_code": "us", "state": "New York", "postcode": "11370-2314"}
        ),
    )
    assert entry.zipcode == "11370"
    assert entry.metro == "New York-Newark-Jersey City"


def test_us_county_from_geocode_does_not_fail_the_record() -> None:
    """Regression: a county name is not a valid state and used to raise in normalize().

    The zip lookup supplies the real state instead.
    """
    entry = build_entry()
    enrich(
        entry,
        coordinates=COORDINATES,
        reverse_geocode=build_geocode(
            {"country_code": "us", "county": "Queens County", "postcode": "11370"}
        ),
    )
    assert entry.state == "NY"
    assert entry.city == "East Elmhurst"
    assert entry.metro == "New York-Newark-Jersey City"


def test_geocoded_city_is_not_overwritten_by_the_zip_lookup() -> None:
    """Geocoding is more precise than the zip database, so it wins."""
    entry = build_entry()
    enrich(entry, coordinates=COORDINATES)
    assert entry.city == "New York"  # not "East Elmhurst"


def test_enriches_from_existing_data_without_coordinates() -> None:
    """Contacts missing from Mailchimp still get normalized and backfilled."""
    entry = build_entry(country="United States", zipcode="11370-2314")
    reverse_fn = build_geocode()
    enrich(entry, coordinates=None, reverse_geocode=reverse_fn)

    assert not reverse_fn.called
    assert entry.country == "USA"
    assert entry.zipcode == "11370"
    assert entry.city == "East Elmhurst"
    assert entry.state == "NY"
    assert entry.metro == "New York-Newark-Jersey City"


def test_non_us_entry_gets_no_metro() -> None:
    entry = build_entry()
    enrich(
        entry,
        coordinates=COORDINATES,
        reverse_geocode=build_geocode(
            {
                "country_code": "gb",
                "state_district": "Greater London",
                "city": "London",
                "postcode": "SW1A 1AA",
            }
        ),
    )
    assert entry.country == "GBR"
    assert entry.state == "Greater London"
    assert entry.city == "London"
    assert entry.zipcode == "SW1A 1AA"
    assert entry.metro is None
