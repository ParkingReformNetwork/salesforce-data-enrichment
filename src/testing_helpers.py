from typing import Any
from unittest.mock import Mock

from salesforce_data_enrichment.salesforce_entry import SalesforceEntry

# A Nominatim reverse-geocode result for a US address. Note that Nominatim returns
# lowercase two-letter country codes and full state names.
US_ADDRESS: dict[str, Any] = {
    "country_code": "us",
    "state": "New York",
    "city": "New York",
    "postcode": "11370",
}


def build_entry(
    *,
    uid: str = "12345",
    email: str | None = "tech@parkingreform.org",
    city: str | None = None,
    country: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    zipcode: str | None = None,
    state: str | None = None,
    street: str | None = None,
    metro: str | None = None,
) -> SalesforceEntry:
    """Build a SalesforceEntry, defaulting every location field to empty."""
    return SalesforceEntry(
        Id=uid,
        Email=email,
        MailingCity=city,
        MailingCountry=country,
        MailingLatitude=latitude,
        MailingLongitude=longitude,
        MailingPostalCode=zipcode,
        MailingState=state,
        MailingStreet=street,
        Metro_Area__c=metro,
    )


def build_geocode(address: dict[str, Any] | None = US_ADDRESS) -> Mock:
    """Build a fake `reverse_geocode` that returns the given Nominatim address.

    Pass `address=None` to simulate Nominatim finding no location at all.
    """
    reverse_fn = Mock()
    if address is None:
        reverse_fn.return_value = None
    else:
        reverse_fn.return_value.raw = {"address": address}
    return reverse_fn
