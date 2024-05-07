from uszipcode import SearchEngine
from pydantic import BaseModel, Field

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
