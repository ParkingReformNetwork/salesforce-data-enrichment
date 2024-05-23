from typing import Optional

from geopy import Nominatim
from uszipcode import SearchEngine
from pydantic import BaseModel, Field

from mailchimp_entry import MailchimpEntry
from state_codes import US_STATES_TO_CODES


class SalesforceEntry(BaseModel):
    email: str = Field(..., alias="Email", frozen=True)
    uid: str = Field(..., alias="Id", frozen=True)
    city: str = Field(..., alias="MailingCity")
    country: str = Field(..., alias="MailingCountry")
    latitude: str = Field(..., alias="MailingLatitude")
    longitude: str = Field(..., alias="MailingLongitude")
    zipcode: str = Field(..., alias="MailingPostalCode")
    state: str = Field(..., alias="MailingState")
    street: str = Field(..., alias="MailingStreet")
    metro: str = Field("", alias="MetropolitanArea")

    @classmethod
    def mock(
        cls,
        *,
        city: Optional[str] = None,
        country: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        zipcode: Optional[str] = None,
        state: Optional[str] = None,
        street: Optional[str] = None,
        metro: Optional[str] = None,
    ) -> "SalesforceEntry":
        return cls(
            Email="tech@parkingreform.org",
            Id="12345",
            MailingCity=city or "",
            MailingCountry=country or "",
            MailingLatitude=latitude or "",
            MailingLongitude=longitude or "",
            MailingPostalCode=zipcode or "",
            MailingState=state or "",
            MailingStreet=street or "",
            MetropolitanArea=metro or "",
        )

    def normalize(self) -> None:
        """Normalize the country code, state, city, and zip.

        This does not add any new data, only normalizes existing data.
        """
        if self.country in ("US", "United States"):
            self.country = "USA"

        # Convert US state names to two-digit codes.
        if self.country == "USA" and len(self.state) > 2:
            self.state = US_STATES_TO_CODES[self.state]

        # Lowercase all-caps city names.
        if self.city.isupper():
            self.city = self.city.title()

        # Normalize US zip codes to be 5 digits.
        if self.country == "USA" and len(self.zipcode) > 5:
            assert self.zipcode[5] == "-"
            self.zipcode = self.zipcode[:5]

    def populate_via_mailchimp(
        self, mailchimp: Optional[MailchimpEntry], geocoder: Nominatim
    ) -> None:
        if mailchimp is None or (
            self.country and self.state and self.city and self.zipcode
        ):
            return

        # Next, reverse geocode the lat/long. This allows us to get a zip code.
        if mailchimp.latitude and mailchimp.longitude:
            self.latitude = mailchimp.latitude
            self.longitude = mailchimp.longitude

            addr = geocoder.reverse(f"{mailchimp.latitude}, {mailchimp.longitude}").raw[
                "address"
            ]
            if not self.country:
                self.country = addr.get("country_code", "").upper()
            if not self.state:
                self.state = addr.get("state", "")
            if not self.city:
                self.city = addr.get("city", "")
            if not self.zipcode:
                self.zipcode = addr.get("postcode", "")
            return

        # Finally, see if the city, state/province, country was set. This data comes from us, not
        # the IP address.
        if mailchimp.city_state_country:
            self.city, self.state, self.country = mailchimp.city_state_country

    def populate_city_via_zipcode(self, zipcode_search_engine: SearchEngine) -> None:
        """Look up city and state for US zip codes."""
        if self.country != "USA" or not self.zipcode or (self.state and self.city):
            return
        zipcode_info = zipcode_search_engine.by_zipcode(self.zipcode)
        if not self.state:
            self.state = zipcode_info.state
        if not self.city:
            self.city = zipcode_info.major_city

    def populate_metro_area(self, us_zip_to_metro_name: dict[str, str]) -> None:
        self.metro = (
            us_zip_to_metro_name.get(self.zipcode, "")
            if self.country == "USA" and self.zipcode
            else ""
        )
