from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from salesforce_data_enrichment.metro_csvs import (
    _cipher,
    parse_us_city_and_state_to_metro,
    parse_us_zip_to_metro,
    read_us_zip_to_metro,
)


def test_parse_us_zip_to_metro_skips_empty_metro() -> None:
    csv_text = "Zip Code,Primary CBSA Name\n11370,New York-Newark-Jersey City\n99999,\n"
    assert parse_us_zip_to_metro(csv_text) == {"11370": "New York-Newark-Jersey City"}


def test_parse_us_city_and_state_to_metro() -> None:
    csv_text = "city,state,metro\nFlushing,NY,New York-Newark-Jersey City\n"
    assert parse_us_city_and_state_to_metro(csv_text) == {
        ("Flushing", "NY"): "New York-Newark-Jersey City"
    }


def test_parse_us_city_and_state_to_metro_skips_empty_metro() -> None:
    """An empty metro would otherwise blank out the record's existing Metro_Area__c."""
    csv_text = (
        "city,state,metro\nFlushing,NY,New York-Newark-Jersey City\nNowhere,AK,\n"
    )
    assert parse_us_city_and_state_to_metro(csv_text) == {
        ("Flushing", "NY"): "New York-Newark-Jersey City"
    }


def test_read_us_zip_to_metro_decrypts_the_csv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    key = Fernet.generate_key()
    csv_text = "Zip Code,Primary CBSA Name\n11370,New York-Newark-Jersey City\n"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "us-zip-to-metro.encrypted.csv").write_bytes(
        Fernet(key).encrypt(csv_text.encode("utf-8"))
    )

    monkeypatch.setenv("ENCRYPTION_KEY", key.decode("utf-8"))
    monkeypatch.chdir(tmp_path)
    _cipher.cache_clear()

    try:
        assert read_us_zip_to_metro() == {"11370": "New York-Newark-Jersey City"}
    finally:
        # The cipher is cached process-wide, so don't leak this key to other tests.
        _cipher.cache_clear()
