from unittest.mock import Mock

import pytest
from uszipcode import SearchEngine

from mailchimp_entry import MailchimpEntry
from salesforce_entry import SalesforceEntry


@pytest.fixture
def geocoder_mock():
    geocoder = Mock()
    reverse_method_mock = Mock()
    reverse_method_mock.raw = {
        "address": {
            "country_code": "USA",
            "state": "NY",
            "city": "New York",
            "postcode": "11370",
        }
    }
    geocoder.reverse.return_value = reverse_method_mock
    return geocoder


@pytest.mark.parametrize(
    "arg,expected",
    [
        ("US", "USA"),
        ("United States", "USA"),
        ("USA", "USA"),
        ("MEX", "MEX"),
    ],
)
def test_normalize_usa_country(arg: str, expected: str) -> None:
    entry = SalesforceEntry.mock(country=arg)
    entry.normalize()
    assert entry.country == expected


@pytest.mark.parametrize(
    "country,state,expected",
    [
        ("USA", "Arizona", "AZ"),
        ("USA", "AZ", "AZ"),
        ("MEX", "Arizona", "Arizona"),
    ],
)
def test_normalize_state(country: str, state: str, expected: str) -> None:
    entry = SalesforceEntry.mock(country=country, state=state)
    entry.normalize()
    assert entry.state == expected


@pytest.mark.parametrize(
    "arg,expected",
    [("ST. PAUL", "St. Paul"), ("St. Paul", "St. Paul")],
)
def test_normalize_city_capitalization(arg: str, expected: str) -> None:
    entry = SalesforceEntry.mock(city=arg)
    entry.normalize()
    assert entry.city == expected


@pytest.mark.parametrize(
    "country,zip,expected",
    [
        ("USA", "11370-2314", "11370"),
        ("USA", "11370", "11370"),
        ("USA", None, None),
        ("MEX", "11370-54", "11370-54"),
    ],
)
def test_normalize_zip_code_length(country: str, zip: str, expected: str) -> None:
    entry = SalesforceEntry.mock(country=country, zipcode=zip)
    entry.normalize()
    assert entry.zipcode == expected


@pytest.mark.parametrize(
    "country,zip,expected_state,expected_city",
    [
        ("USA", "11370", "NY", "East Elmhurst"),
        ("MEX", "11370", None, None),
    ],
)
def test_populate_via_zipcode(
    country: str, zip: str, expected_state: str, expected_city: str
) -> None:
    entry = SalesforceEntry.mock(country=country, zipcode=zip)
    entry.populate_via_zipcode(SearchEngine())
    assert entry.state == expected_state
    assert entry.city == expected_city


def test_populate_via_lat_long(geocoder_mock) -> None:
    mailchimp = MailchimpEntry.mock(latitude="1.1", longitude="'4.2")
    entry = SalesforceEntry.mock()
    entry.populate_via_latitude_longitude(mailchimp, geocoder_mock)
    assert entry.city == "New York"
    assert entry.state == "NY"
    assert entry.country == "USA"
    assert entry.zipcode == "11370"
    assert entry.latitude == "1.1"
    assert entry.longitude == "4.2"


@pytest.mark.parametrize(
    "country,zip,city,state,expected",
    [
        ("USA", "11370", "Flushing", "NY", "My Metro"),
        ("USA", "99999", "Flushing", "NY", None),
        ("USA", None, "Tempe", "AZ", "My Metro"),
        ("USA", None, None, None, None),
        ("MEX", "11370", "Tempe", "AZ", None),
    ],
)
def test_populate_metro_area(
    country: str, zip: str, city: str, state: str, expected: str
) -> None:
    entry = SalesforceEntry.mock(country=country, zipcode=zip, city=city, state=state)
    entry.populate_metro_area({"11370": "My Metro"}, {("Tempe", "AZ"): "My Metro"})
    assert entry.metro == expected


def test_compute_changes() -> None:
    entry = SalesforceEntry.mock()
    original_model_dump = entry.model_dump(by_alias=True)

    assert not entry.compute_changes(original_model_dump)

    entry.city = "My City"
    entry.zipcode = "11370"
    updates = {"MailingCity": "My City", "MailingPostalCode": "11370"}
    assert entry.compute_changes(original_model_dump) == updates
    updated_model_dump = entry.model_dump(by_alias=True)

    entry.country = "USA"
    country_update = {"MailingCountry": "USA"}
    assert entry.compute_changes(original_model_dump) == {**updates, **country_update}
    assert entry.compute_changes(updated_model_dump) == country_update
