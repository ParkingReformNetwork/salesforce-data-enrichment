from salesforce_data_enrichment.us_zip_lookup import parse_us_zip_to_city_state


def test_parse_us_zip_to_city_state() -> None:
    csv_text = "zip,city,state\n11370,East Elmhurst,NY\n85281,Tempe,AZ\n"
    assert parse_us_zip_to_city_state(csv_text) == {
        "11370": ("East Elmhurst", "NY"),
        "85281": ("Tempe", "AZ"),
    }


def test_parse_us_zip_to_city_state_keeps_leading_zeros() -> None:
    """Zip codes are strings, not numbers: 07087 must not become 7087."""
    csv_text = "zip,city,state\n07087,Union City,NJ\n"
    assert parse_us_zip_to_city_state(csv_text) == {"07087": ("Union City", "NJ")}
