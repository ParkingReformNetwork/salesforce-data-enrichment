import pytest
from testing_helpers import build_entry, build_geocode

from salesforce_data_enrichment.mailchimp_coordinates import Coordinates

COORDINATES = Coordinates(latitude=1.1, longitude=4.2)


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
    entry = build_entry(country=arg)
    entry.normalize()
    assert entry.country == expected


@pytest.mark.parametrize("arg", ["ZZ", "Fake Country"])
def test_normalize_country_unrecognized_raises(arg: str) -> None:
    entry = build_entry(country=arg)
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
    entry = build_entry(country=country, state=state)
    entry.normalize()
    assert entry.state == expected


def test_normalize_state_unrecognized_raises() -> None:
    entry = build_entry(country="USA", state="Fake State")
    with pytest.raises(ValueError):
        entry.normalize()


@pytest.mark.parametrize(
    "arg,expected",
    [("ST. PAUL", "St. Paul"), ("St. Paul", "St. Paul")],
)
def test_normalize_city_capitalization(arg: str, expected: str) -> None:
    entry = build_entry(city=arg)
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
def test_normalize_zip_code_length(
    country: str, zip: str | None, expected: str | None
) -> None:
    entry = build_entry(country=country, zipcode=zip)
    entry.normalize()
    assert entry.zipcode == expected


@pytest.mark.parametrize("zip", ["1137", "1137023", "abcde", "113a2"])
def test_normalize_zip_code_invalid_raises(zip: str) -> None:
    entry = build_entry(country="USA", zipcode=zip)
    with pytest.raises(ValueError) as exc_info:
        entry.normalize()
    assert zip not in str(exc_info.value)


# -------------------------------------------------------
# populate_via_us_zipcode
# -------------------------------------------------------

_US_ZIP_TO_CITY_STATE = {"11370": ("East Elmhurst", "NY")}


@pytest.mark.parametrize(
    "country,zip,expected_state,expected_city",
    [
        ("USA", "11370", "NY", "East Elmhurst"),
        ("MEX", "11370", None, None),
        ("USA", "00000", None, None),  # zip not in the lookup table
    ],
)
def test_populate_via_zipcode(
    country: str, zip: str, expected_state: str | None, expected_city: str | None
) -> None:
    entry = build_entry(country=country, zipcode=zip)
    entry.populate_via_us_zipcode(_US_ZIP_TO_CITY_STATE)
    assert entry.state == expected_state
    assert entry.city == expected_city


def test_populate_via_zipcode_does_not_overwrite_existing_city_and_state() -> None:
    entry = build_entry(country="USA", zipcode="11370", city="Flushing", state="NY")
    entry.populate_via_us_zipcode(_US_ZIP_TO_CITY_STATE)
    assert entry.city == "Flushing"
    assert entry.state == "NY"


# -------------------------------------------------------
# populate_via_coordinates
# -------------------------------------------------------


def test_populate_via_coordinates() -> None:
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, build_geocode())
    assert entry.city == "New York"
    assert entry.zipcode == "11370"
    assert entry.latitude == 1.1
    assert entry.longitude == 4.2
    # Raw Nominatim values; normalize() converts these to "USA" and "NY" afterwards.
    assert entry.country == "US"
    assert entry.state == "New York"


def test_populate_via_coordinates_clears_street() -> None:
    """The old street belongs to the old address, so it must not survive."""
    entry = build_entry(street="123 Fake St")
    entry.populate_via_coordinates(COORDINATES, build_geocode())
    assert entry.street is None


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
    country: str,
    zip: str | None,
    city: str | None,
    state: str | None,
    should_geocode: bool,
) -> None:
    reverse_fn = build_geocode()
    entry = build_entry(country=country, zipcode=zip, city=city, state=state)
    entry.populate_via_coordinates(COORDINATES, reverse_fn)

    assert reverse_fn.called == should_geocode
    if not should_geocode:
        # Skipping the lookup must also leave the existing data untouched.
        assert (entry.country, entry.zipcode, entry.city, entry.state) == (
            country,
            zip,
            city,
            state,
        )
        assert entry.latitude is None
        assert entry.longitude is None


def test_populate_via_coordinates_skips_when_no_coordinates() -> None:
    """Most contacts have no Mailchimp coordinates; they must not cost a lookup."""
    reverse_fn = build_geocode()
    entry = build_entry()
    entry.populate_via_coordinates(None, reverse_fn)
    assert not reverse_fn.called
    assert entry.zipcode is None


@pytest.mark.parametrize(
    "addr_key",
    ["city", "town", "municipality", "village", "hamlet"],
)
def test_populate_via_coordinates_city_fallback(addr_key: str) -> None:
    reverse_fn = build_geocode(
        {
            "country_code": "us",
            "state": "New York",
            addr_key: "Small Place",
            "postcode": "11370",
        }
    )
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, reverse_fn)
    assert entry.city == "Small Place"


@pytest.mark.parametrize(
    "addr_key",
    ["state", "region", "state_district", "county"],
)
def test_populate_via_coordinates_state_fallback(addr_key: str) -> None:
    reverse_fn = build_geocode(
        {
            "country_code": "gb",
            addr_key: "Some Region",
            "city": "London",
            "postcode": "SW1A 1AA",
        }
    )
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, reverse_fn)
    assert entry.state == "Some Region"


@pytest.mark.parametrize("addr_key", ["region", "state_district", "county"])
def test_populate_via_coordinates_ignores_us_state_fallbacks(addr_key: str) -> None:
    """A US county or district is not a valid MailingState, so it must be dropped."""
    reverse_fn = build_geocode(
        {"country_code": "us", addr_key: "Queens County", "postcode": "11370"}
    )
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, reverse_fn)
    assert entry.state is None


def test_populate_via_coordinates_skips_when_geocode_returns_none() -> None:
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, build_geocode(address=None))
    assert entry.zipcode is None
    assert entry.latitude is None
    assert entry.longitude is None


def test_populate_via_coordinates_skips_when_no_postcode_found() -> None:
    entry = build_entry()
    entry.populate_via_coordinates(COORDINATES, build_geocode({"city": "New York"}))
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
    country: str,
    zip: str | None,
    city: str | None,
    state: str | None,
    expected: str | None,
) -> None:
    entry = build_entry(country=country, zipcode=zip, city=city, state=state)
    entry.populate_us_metro_area({"11370": "My Metro"}, {("Tempe", "AZ"): "My Metro"})
    assert entry.metro == expected


def test_populate_metro_area_keeps_existing_metro_when_lookup_misses() -> None:
    entry = build_entry(country="USA", zipcode="99999", metro="Old Metro")
    entry.populate_us_metro_area({"11370": "My Metro"}, {})
    assert entry.metro == "Old Metro"


# -------------------------------------------------------
# compute_changes
# -------------------------------------------------------


def test_compute_changes_empty_when_unmodified() -> None:
    entry = build_entry()
    assert not entry.compute_changes(entry.model_dump(by_alias=True))


def test_compute_changes_reports_modified_fields() -> None:
    entry = build_entry()
    original = entry.model_dump(by_alias=True)

    entry.city = "My City"
    entry.zipcode = "11370"

    assert entry.compute_changes(original) == {
        "MailingCity": "My City",
        "MailingPostalCode": "11370",
    }


def test_compute_changes_is_relative_to_the_given_dump() -> None:
    entry = build_entry()
    original = entry.model_dump(by_alias=True)
    entry.city = "My City"
    intermediate = entry.model_dump(by_alias=True)

    entry.country = "USA"

    assert entry.compute_changes(original) == {
        "MailingCity": "My City",
        "MailingCountry": "USA",
    }
    assert entry.compute_changes(intermediate) == {"MailingCountry": "USA"}


def test_compute_changes_includes_cleared_fields() -> None:
    """Nulling a field is a real change that must be written back."""
    entry = build_entry(street="123 Fake St")
    original = entry.model_dump(by_alias=True)

    entry.street = None

    assert entry.compute_changes(original) == {"MailingStreet": None}


def test_compute_changes_includes_float_coordinates() -> None:
    entry = build_entry()
    original = entry.model_dump(by_alias=True)

    entry.latitude = 1.1

    assert entry.compute_changes(original) == {"MailingLatitude": 1.1}
