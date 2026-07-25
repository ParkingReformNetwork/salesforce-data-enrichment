from collections.abc import Callable

from geopy.location import Location
from pydantic import BaseModel, Field

from salesforce_data_enrichment.mailchimp_coordinates import Coordinates
from salesforce_data_enrichment.reference_data.country_codes import (
    COUNTRY_CODES_TWO_LETTER_TO_THREE,
    COUNTRY_NAMES_TO_THREE,
)
from salesforce_data_enrichment.reference_data.state_codes import US_STATES_TO_CODES

FieldValue = str | float | None

ReverseGeocode = Callable[[str], Location | None]


class SalesforceEntry(BaseModel):
    uid: str = Field(..., alias="Id", frozen=True)
    email: str | None = Field(..., alias="Email", frozen=True)
    city: str | None = Field(..., alias="MailingCity")
    country: str | None = Field(..., alias="MailingCountry")
    latitude: float | None = Field(..., alias="MailingLatitude")
    longitude: float | None = Field(..., alias="MailingLongitude")
    zipcode: str | None = Field(..., alias="MailingPostalCode")
    state: str | None = Field(..., alias="MailingState")
    street: str | None = Field(..., alias="MailingStreet")
    metro: str | None = Field(..., alias="Metro_Area__c")

    def compute_changes(
        self, original_model_dump: dict[str, FieldValue]
    ) -> dict[str, FieldValue]:
        new_model_dump = self.model_dump(by_alias=True)
        return {k: v for k, v in new_model_dump.items() if v != original_model_dump[k]}

    def _normalized_country(self) -> str | None:
        if not self.country:
            return None
        if len(self.country) == 2:
            country = self.country.upper()
            if country not in COUNTRY_CODES_TWO_LETTER_TO_THREE:
                raise ValueError(f"Unrecognized country '{country}' for {self.uid}")
            return COUNTRY_CODES_TWO_LETTER_TO_THREE[country]
        if len(self.country) > 3:
            if self.country not in COUNTRY_NAMES_TO_THREE:
                raise ValueError(
                    f"Unrecognized country '{self.country}' for {self.uid}"
                )
            return COUNTRY_NAMES_TO_THREE[self.country]
        return self.country

    def normalize(self) -> None:
        """Normalize the country code, state, city, and zip.

        This does not add any new data, only normalizes existing data.
        """
        if self.country:
            self.country = self._normalized_country()

        # Convert US state names to two-digit codes.
        if self.country == "USA" and self.state and len(self.state) > 2:
            if self.state not in US_STATES_TO_CODES:
                raise ValueError(f"Unrecognized state {self.state} for {self.uid}")
            self.state = US_STATES_TO_CODES[self.state]

        # Lowercase all-caps city names.
        if self.city and self.city.isupper():
            self.city = self.city.title()

        # Normalize US zip codes (5 digits) and zip+4 codes (e.g. "11370-2314" or
        # "070876603") down to 5 digits. Reject anything else.
        if self.country == "USA" and self.zipcode:
            digits = self.zipcode.replace("-", "")
            if len(digits) not in (5, 9) or not digits.isdigit():
                # We don't log the actual zip code because it's personal information.
                raise ValueError(f"Malformed MailingPostalCode for uid {self.uid}")
            self.zipcode = digits[:5]

    def populate_via_coordinates(
        self, coordinates: Coordinates | None, reverse_geocode: ReverseGeocode
    ) -> None:
        if coordinates is None:
            return

        is_usa = self._normalized_country() == "USA"
        # A US zip is enough on its own: populate_us_metro_area looks up the metro
        # directly from it, and populate_via_us_zipcode backfills city/state from a
        # local database. Neither needs a reverse geocode lookup.
        if is_usa and self.zipcode:
            return
        if is_usa and self.city and self.state:
            return

        # For non-US, it's enough for us to know their city + country; no need to geocode.
        if not is_usa and self.city and self.country:
            return

        location = reverse_geocode(f"{coordinates.latitude}, {coordinates.longitude}")
        if location is None:
            return
        addr = location.raw.get("address")
        if not addr or "postcode" not in addr:
            return

        self.latitude = coordinates.latitude
        self.longitude = coordinates.longitude
        self.zipcode = addr["postcode"]

        # Also overwrite any existing values so that we don't mix the prior address
        # with the new one.
        self.street = None
        self.country = addr.get("country_code", "").upper() or None

        self.state = addr.get("state")
        if not self.state and self.country != "US":
            self.state = (
                addr.get("region") or addr.get("state_district") or addr.get("county")
            )

        self.city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("municipality")
            or addr.get("village")
            or addr.get("hamlet")
        )

    def populate_via_us_zipcode(
        self, us_zip_to_city_state: dict[str, tuple[str, str]]
    ) -> None:
        """Look up city and state for US zip codes."""
        if self.country != "USA" or not self.zipcode or (self.state and self.city):
            return
        city_state = us_zip_to_city_state.get(self.zipcode)
        if city_state:
            self.city, self.state = city_state

    def populate_us_metro_area(
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
