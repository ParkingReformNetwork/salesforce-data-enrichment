from metro_csvs import parse_us_city_and_state_to_metro, parse_us_zip_to_metro


def test_parse_us_zip_to_metro_skips_empty_metro() -> None:
    csv_text = "Zip Code,Primary CBSA Name\n11370,New York-Newark-Jersey City\n99999,\n"
    assert parse_us_zip_to_metro(csv_text) == {"11370": "New York-Newark-Jersey City"}


def test_parse_us_city_and_state_to_metro() -> None:
    csv_text = "city,state,metro\nFlushing,NY,New York-Newark-Jersey City\n"
    assert parse_us_city_and_state_to_metro(csv_text) == {
        ("Flushing", "NY"): "New York-Newark-Jersey City"
    }
