from refresh_us_zip_data import parse_zip_to_city_state

# GeoNames' US.txt is tab-separated with no header:
# country, zip, city, state name, state code, then columns we don't use.


def _row(zipcode: str, city: str, state_code: str) -> str:
    return f"US\t{zipcode}\t{city}\tState Name\t{state_code}\textra\tcolumns\there"


def test_parse_zip_to_city_state() -> None:
    us_txt = "\n".join(
        [_row("11370", "East Elmhurst", "NY"), _row("85281", "Tempe", "AZ")]
    )
    assert parse_zip_to_city_state(us_txt) == {
        "11370": ("East Elmhurst", "NY"),
        "85281": ("Tempe", "AZ"),
    }


def test_parse_zip_to_city_state_keeps_first_of_duplicate_zips() -> None:
    """Some zip codes (e.g. military ones) appear on several rows."""
    us_txt = "\n".join([_row("09001", "APO", "AE"), _row("09001", "Other", "AE")])
    assert parse_zip_to_city_state(us_txt) == {"09001": ("APO", "AE")}


def test_parse_zip_to_city_state_ignores_trailing_columns() -> None:
    """Only the first five columns are used, and GeoNames may add more."""
    us_txt = "US\t11370\tEast Elmhurst\tNew York\tNY\t" + "\t".join(["x"] * 10)
    assert parse_zip_to_city_state(us_txt) == {"11370": ("East Elmhurst", "NY")}
