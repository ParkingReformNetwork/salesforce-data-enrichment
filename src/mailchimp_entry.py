from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MailchimpEntry(BaseModel):
    email: str = Field(..., alias="Email Address")
    address: str = Field(..., alias="Address")
    latitude: str = Field(..., alias="LATITUDE")
    longitude: str = Field(..., alias="LONGITUDE")
    city_state_country: Optional[tuple[str, str, str]] = Field(
        ..., alias="City, State/Province, Country"
    )

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, v: str) -> str:
        return v.lstrip("'")

    @field_validator("city_state_country", mode="before")
    @classmethod
    def parse_city_state_country(cls, v: str) -> Optional[tuple[str, str, str]]:
        split = v.split(",")
        if len(split) != 3:
            return None
        return split[0].strip(), split[1].strip(), split[2].strip()
