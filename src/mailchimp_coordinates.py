import logging
import os
from typing import Any, NamedTuple

from mailchimp3 import MailChimp

logging.getLogger("mailchimp3.client").setLevel(logging.CRITICAL)


class Coordinates(NamedTuple):
    latitude: str
    longitude: str

    @classmethod
    def from_mailchimp(cls, entry: dict[str, Any]) -> "Coordinates | None":
        lat: float = entry["location"]["latitude"]
        long: float = entry["location"]["longitude"]
        return cls(str(lat), str(long)) if lat and long else None


def get_coordinates_by_email() -> dict[str, Coordinates | None]:
    key = os.environ.pop("MAILCHIMP_KEY")
    list_id = os.environ.pop("MAILCHIMP_LIST_ID")
    client = MailChimp(mc_api=key)
    result = client.lists.members.all(
        list_id=list_id,
        fields="members.email_address,members.location.latitude,members.location.longitude",
        get_all=True,
    )["members"]
    return {
        entry["email_address"]: coords
        for entry in result
        if (coords := Coordinates.from_mailchimp(entry)) is not None
    }
