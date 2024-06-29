import os

from simple_salesforce import Salesforce

from salesforce_entry import SalesforceEntry


def init_client() -> Salesforce:
    USERNAME = os.environ.pop("SALESFORCE_USERNAME")
    PASSWORD = os.environ.pop("SALESFORCE_PASSWORD")
    TOKEN = os.environ.pop("SALESFORCE_TOKEN")
    return Salesforce(
        username=USERNAME,
        password=PASSWORD,
        security_token=TOKEN,
        client_id="salesforce-data-enrichment",
    )


def load_data(client: Salesforce) -> list[SalesforceEntry]:
    fields = ", ".join(
        info.alias or name for name, info in SalesforceEntry.model_fields.items()
    )
    return [
        SalesforceEntry(**raw)
        for raw in client.query_all_iter(f"SELECT {fields} FROM Contact")
    ]


def write_change(client: Salesforce, uid: str, changes: dict[str, str]) -> None:
    client.Contact.update(uid, changes)  # type: ignore[operator]
