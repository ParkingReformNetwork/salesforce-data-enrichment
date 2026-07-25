from simple_salesforce import Salesforce

from salesforce_data_enrichment.env import pop_env
from salesforce_data_enrichment.salesforce_entry import SalesforceEntry


def init_client() -> Salesforce:
    username, password, token = pop_env(
        "SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_TOKEN"
    )
    return Salesforce(
        username=username,
        password=password,
        security_token=token,
        client_id="salesforce-data-enrichment",
    )


def query_fields() -> str:
    return ", ".join(
        info.alias or name for name, info in SalesforceEntry.model_fields.items()
    )


def load_data(client: Salesforce) -> list[SalesforceEntry]:
    return [
        SalesforceEntry(**raw)
        for raw in client.query_all_iter(f"SELECT {query_fields()} FROM Contact")
    ]


def write_change(client: Salesforce, uid: str, changes: dict[str, str]) -> None:
    # We don't use the bulk API because error messages are bad and we only write a
    # handful of records per run.
    client.Contact.update(uid, changes)  # ty: ignore[call-non-callable]
