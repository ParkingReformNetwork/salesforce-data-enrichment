from unittest.mock import Mock

import pytest
from uszipcode import SearchEngine

from salesforce_data_enrichment.mailchimp_coordinates import Coordinates
from salesforce_data_enrichment.salesforce_entry import SalesforceEntry


@pytest.fixture
def geocode_reverse_mock():
    reverse_fn = Mock()
    reverse_method_mock = Mock()
    reverse_method_mock.raw = {
        "address": {
            "country_code": "USA",
            "state": "NY",
            "city": "New York",
            "postcode": "11370",
        }
    }
    reverse_fn.return_value = reverse_method_mock
    return reverse_fn


# -------------------------------------------------------
# normalize
# -------------------------------------------------------


@pytest.mark.parametrize(
    "arg,expected",
    [
        ("US", "USA"),
        ("AG", "ATG"),
        ("United States", "USA"),
        ("India", "IND"),
        ("USA", "USA"),
        ("MEX", "MEX"),
    ],
)
def test_normalize_country(arg: str, expected: str) -> None:
    entry = SalesforceEntry.mock(country=arg)
    entry.normalize()
    assert entry.country == expected


@pytest.mark.parametrize("arg", ["ZZ", "Fake Country"])
def test_normalize_country_unrecognized_raises(arg: str) -> None:
    entry = SalesforceEntry.mock(country=arg)
    with pytest.raises(ValueError):
        entry.normalize()


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


def test_normalize_state_unrecognized_raises() -> None:
    entry = SalesforceEntry.mock(country="USA", state="Fake State")
    with pytest.raises(ValueError):
        entry.normalize()


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
        ("USA", "113702314", "11370"),
        ("USA", "07087-6603", "07087"),
        ("USA", "070876603", "07087"),
        ("USA", "11370", "11370"),
        ("USA", None, None),
        ("MEX", "11370-54", "11370-54"),
    ],
)
def test_normalize_zip_code_length(country: str, zip: str, expected: str) -> None:
    entry = SalesforceEntry.mock(country=country, zipcode=zip)
    entry.normalize()
    assert entry.zipcode == expected


@pytest.mark.parametrize("zip", ["1137", "1137023", "abcde", "113a2"])
def test_normalize_zip_code_invalid_raises(zip: str) -> None:
    entry = SalesforceEntry.mock(country="USA", zipcode=zip)
    with pytest.raises(ValueError):
        entry.normalize()


# -------------------------------------------------------
# populate_via_us_zipcode
# -------------------------------------------------------


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
    entry.populate_via_us_zipcode(SearchEngine())
    assert entry.state == expected_state
    assert entry.city == expected_city


# -------------------------------------------------------
# populate_via_coordinates
# -------------------------------------------------------


def test_populate_via_coordinates(geocode_reverse_mock) -> None:
    coordinates = Coordinates(latitude=1.1, longitude=4.2)
    entry = SalesforceEntry.mock()
    entry.populate_via_coordinates(coordinates, geocode_reverse_mock)
    assert entry.city == "New York"
    assert entry.state == "NY"
    assert entry.country == "USA"
    assert entry.zipcode == "11370"
    assert entry.latitude == 1.1
    assert entry.longitude == 4.2


@pytest.mark.parametrize(
    "country,zip,city,state,should_geocode",
    [
        # USA: a zip alone is enough (metro CSV / local DB cover the rest).
        ("USA", "11370", None, None, False),
        # USA: city + state is enough for the metro lookup.
        ("USA", None, "Flushing", "NY", False),
        # USA: city alone can't find a metro without state or zip.
        ("USA", None, "Flushing", None, True),
        # USA: state alone can't find a metro without city or zip.
        ("USA", None, None, "NY", True),
        # Non-USA: city + country is enough; metro never applies there.
        ("GB", None, "London", None, False),
        # Non-USA: a zip alone can't fill in city without geocoding (no local DB).
        ("GB", "SW1A 1AA", None, None, True),
        # Non-USA: country alone can't fill in city without geocoding.
        ("GB", None, None, None, True),
    ],
)
def test_populate_via_coordinates_geocode_guard(
    geocode_reverse_mock,
    country: str,
    zip: str | None,
    city: str | None,
    state: str | None,
    should_geocode: bool,
) -> None:
    coordinates = Coordinates(latitude=1.1, longitude=4.2)
    entry = SalesforceEntry.mock(country=country, zipcode=zip, city=city, state=state)
    entry.populate_via_coordinates(coordinates, geocode_reverse_mock)
    assert geocode_reverse_mock.called == should_geocode


@pytest.mark.parametrize(
    "addr_key",
    ["city", "town", "municipality", "village", "hamlet"],
)
def test_populate_via_coordinates_city_fallback(addr_key: str) -> None:
    reverse_fn = Mock()
    reverse_fn.return_value.raw = {
        "address": {
            "country_code": "USA",
            "state": "NY",
            addr_key: "Small Place",
            "postcode": "11370",
        }
    }
    coordinates = Coordinates(latitude=1.1, longitude=4.2)
    entry = SalesforceEntry.mock()
    entry.populate_via_coordinates(coordinates, reverse_fn)
    assert entry.city == "Small Place"


@pytest.mark.parametrize(
    "addr_key",
    ["state", "region", "state_district", "county"],
)
def test_populate_via_coordinates_state_fallback(addr_key: str) -> None:
    reverse_fn = Mock()
    reverse_fn.return_value.raw = {
        "address": {
            "country_code": "GB",
            addr_key: "Some Region",
            "city": "London",
            "postcode": "SW1A 1AA",
        }
    }
    coordinates = Coordinates(latitude=1.1, longitude=4.2)
    entry = SalesforceEntry.mock()
    entry.populate_via_coordinates(coordinates, reverse_fn)
    assert entry.state == "Some Region"


def test_populate_via_coordinates_skips_when_no_postcode_found() -> None:
    reverse_fn = Mock()
    reverse_fn.return_value.raw = {"address": {"city": "New York"}}
    coordinates = Coordinates(latitude=1.1, longitude=4.2)
    entry = SalesforceEntry.mock()
    entry.populate_via_coordinates(coordinates, reverse_fn)
    assert entry.zipcode is None
    assert entry.latitude is None
    assert entry.longitude is None


# -------------------------------------------------------
# populate_us_metro_area
# -------------------------------------------------------


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
    entry.populate_us_metro_area({"11370": "My Metro"}, {("Tempe", "AZ"): "My Metro"})
    assert entry.metro == expected


# -------------------------------------------------------
# compute_changes
# -------------------------------------------------------


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
