import os

from simple_salesforce import Salesforce

from salesforce_entry import SalesforceEntry


def init_client() -> Salesforce:
    INSTANCE_URL = os.environ.pop("SALESFORCE_INSTANCE_URL")
    TOKEN = os.environ.pop("SALESFORCE_TOKEN")
    return Salesforce(instance_url=INSTANCE_URL, session_id=TOKEN)


def load_data(client: Salesforce) -> list[SalesforceEntry]:
    fields = ", ".join(
        info.alias or name for name, info in SalesforceEntry.model_fields.items()
    )
    return [
        SalesforceEntry(**raw)
        for raw in client.query_all_iter(f"SELECT {fields} FROM Contact")
    ]


def write_changes(
    client: Salesforce, uid_to_changes: dict[str, dict[str, str]]
) -> None:
    for uid, changes in uid_to_changes.items():
        client.Contact.update(uid, changes)  # type: ignore[operator]
