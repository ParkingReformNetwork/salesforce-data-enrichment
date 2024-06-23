from pydantic import BaseModel, Field, field_validator


class MailchimpEntry(BaseModel):
    email: str = Field(..., alias="Email Address")
    latitude: str = Field(..., alias="LATITUDE")
    longitude: str = Field(..., alias="LONGITUDE")

    @field_validator("latitude")
    @classmethod
    def normalize_latitude(cls, v: str) -> str:
        return v.lstrip("'")

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, v: str) -> str:
        return v.lstrip("'")

    @classmethod
    def mock(
        cls,
        *,
        latitude: str | None = None,
        longitude: str | None = None,
    ) -> "MailchimpEntry":
        return cls(
            **{
                "Email Address": "",
                "LATITUDE": latitude or "",
                "LONGITUDE": longitude or "",
            }
        )
