from pydantic import BaseModel, Field


class SalesforceEntry(BaseModel):
    email: str = Field(..., alias="Email", frozen=True)
    uid: str = Field(..., alias="Id", frozen=True)
    city: str = Field(..., alias="MailingCity")
    country: str = Field(..., alias="MailingCountry")
    latitude: str = Field(..., alias="MailingLatitude")
    longitude: str = Field(..., alias="MailingLongitude")
    zip: str = Field(..., alias="MailingPostalCode")
    state: str = Field(..., alias="MailingState")
    street: str = Field(..., alias="MailingStreet")
    metro: str = Field("", alias="MetropolitanArea")
