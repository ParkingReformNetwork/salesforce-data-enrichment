from geopy import Nominatim
from uszipcode import SearchEngine
from pydantic import BaseModel, Field

from mailchimp_entry import MailchimpEntry
from country_codes import COUNTRY_CODES_TWO_LETTER_TO_THREE, COUNTRY_NAMES_TO_THREE
from state_codes import US_STATES_TO_CODES


class SalesforceEntry(BaseModel):
    uid: str = Field(..., alias="Id", frozen=True)
    email: str | None = Field(..., alias="Email", frozen=True)
    city: str | None = Field(..., alias="MailingCity")
    country: str | None = Field(..., alias="MailingCountry")
    latitude: str | None = Field(..., alias="MailingLatitude")
    longitude: str | None = Field(..., alias="MailingLongitude")
    zipcode: str | None = Field(..., alias="MailingPostalCode")
    state: str | None = Field(..., alias="MailingState")
    street: str | None = Field(..., alias="MailingStreet")
    metro: str | None = Field(..., alias="Metro_Area__c")

    @classmethod
    def mock(
        cls,
        *,
        city: str | None = None,
        country: str | None = None,
        latitude: str | None = None,
        longitude: str | None = None,
        zipcode: str | None = None,
        state: str | None = None,
        street: str | None = None,
        metro: str | None = None,
    ) -> "SalesforceEntry":
        return cls(
            Email="tech@parkingreform.org",
            Id="12345",
            MailingCity=city,
            MailingCountry=country,
            MailingLatitude=latitude,
            MailingLongitude=longitude,
            MailingPostalCode=zipcode,
            MailingState=state,
            MailingStreet=street,
            Metro_Area__c=metro,
        )

    def compute_changes(self, original_model_dump: dict[str, str]) -> dict[str, str]:
        new_model_dump = self.model_dump(by_alias=True)
        return {k: v for k, v in new_model_dump.items() if v != original_model_dump[k]}

    def normalize(self) -> None:
        """Normalize the country code, state, city, and zip.

        This does not add any new data, only normalizes existing data.
        """
        if self.country:
            if len(self.country) == 2:
                country = self.country.upper()
                if country not in COUNTRY_CODES_TWO_LETTER_TO_THREE:
                    raise ValueError(f"Unrecognized country '{country}' for {self.uid}")
                self.country = COUNTRY_CODES_TWO_LETTER_TO_THREE[country]
            elif len(self.country) > 3:
                if self.country not in COUNTRY_NAMES_TO_THREE:
                    raise ValueError(
                        f"Unrecognized country '{self.country}' for {self.uid}"
                    )
                self.country = COUNTRY_NAMES_TO_THREE[self.country]

        # Convert US state names to two-digit codes.
        if self.country == "USA" and self.state and len(self.state) > 2:
            if self.state not in US_STATES_TO_CODES:
                raise ValueError(f"Unrecognized state {self.state} for {self.uid}")
            self.state = US_STATES_TO_CODES[self.state]

        # Lowercase all-caps city names.
        if self.city and self.city.isupper():
            self.city = self.city.title()

        # Normalize US zip codes to be 5 digits.
        if self.country == "USA" and self.zipcode and len(self.zipcode) > 5:
            if self.zipcode[5] != "-":
                raise AssertionError(f"Unexpected zipcode for {self}")
            self.zipcode = self.zipcode[:5]

    def populate_via_latitude_longitude(
        self, mailchimp: MailchimpEntry | None, geocoder: Nominatim
    ) -> None:
        if mailchimp is None or not (mailchimp.latitude and mailchimp.longitude):
            return

        metro_area_can_be_computed = self.zipcode or (self.city and self.country)
        if metro_area_can_be_computed:
            return

        addr = geocoder.reverse(f"{mailchimp.latitude}, {mailchimp.longitude}").raw[
            "address"
        ]
        if "postcode" not in addr:
            return

        self.latitude = mailchimp.latitude
        self.longitude = mailchimp.longitude
        self.zipcode = addr["postcode"]

        # Also overwrite any existing values so that we don't mix the prior address
        # with the new one.
        self.street = None
        self.country = addr.get("country_code", "").upper() or None
        self.state = addr.get("state")
        self.city = addr.get("city")

    def populate_via_zipcode(self, zipcode_search_engine: SearchEngine) -> None:
        """Look up city and state for US zip codes."""
        if self.country != "USA" or not self.zipcode or (self.state and self.city):
            return
        zipcode_info = zipcode_search_engine.by_zipcode(self.zipcode)
        if zipcode_info:
            self.state = zipcode_info.state
            self.city = zipcode_info.major_city

    def populate_metro_area(
        self,
        us_zip_to_metro: dict[str, str],
        us_city_and_state_to_metro: dict[tuple[str, str], str],
    ) -> None:
        if self.country != "USA":
            return

        new_metro = None
        if self.zipcode:
            new_metro = us_zip_to_metro.get(self.zipcode)
        elif self.city and self.state:
            new_metro = us_city_and_state_to_metro.get((self.city, self.state))

        if new_metro is not None:
            self.metro = new_metro
