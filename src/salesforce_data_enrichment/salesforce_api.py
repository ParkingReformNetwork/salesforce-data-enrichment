from simple_salesforce import Salesforce

from salesforce_data_enrichment.env import pop_env
from salesforce_data_enrichment.salesforce_entry import FieldValue, SalesforceEntry


def init_client() -> Salesforce:
    # OAuth 2.0 client credentials flow via an External Client App. The SOAP
    # login() call that username + password + security token used is being
    # retired by Salesforce (Summer '27).
    consumer_key, consumer_secret, domain = pop_env(
        "SALESFORCE_CONSUMER_KEY", "SALESFORCE_CONSUMER_SECRET", "SALESFORCE_DOMAIN"
    )
    return Salesforce(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        domain=normalize_domain(domain),
    )


def normalize_domain(domain: str) -> str:
    """Accept the My Domain as shown in Setup and return the form simple-salesforce
    expects: `https://example.my.salesforce.com/` -> `example.my`.

    The client credentials flow only works against the org's My Domain, never
    the generic `login`/`test` hosts.
    """
    result = domain.strip().removeprefix("https://").rstrip("/")
    result = result.removesuffix(".salesforce.com")
    if result in ("login", "test", "") or "." not in result:
        raise ValueError(
            "SALESFORCE_DOMAIN must be the org's My Domain, e.g. example.my.salesforce.com"
        )
    return result


def query_fields() -> str:
    return ", ".join(
        info.alias or name for name, info in SalesforceEntry.model_fields.items()
    )


def load_data(client: Salesforce) -> list[SalesforceEntry]:
    return [
        SalesforceEntry(**raw)
        for raw in client.query_all_iter(f"SELECT {query_fields()} FROM Contact")
    ]


def write_change(client: Salesforce, uid: str, changes: dict[str, FieldValue]) -> None:
    # We don't use the bulk API because error messages are bad and we only write a
    # handful of records per run.
    client.Contact.update(uid, changes)  # ty: ignore[call-non-callable]
