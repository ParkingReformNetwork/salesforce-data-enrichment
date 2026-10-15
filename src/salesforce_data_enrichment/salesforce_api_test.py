import pytest

from salesforce_data_enrichment.salesforce_api import normalize_domain, query_fields


def test_query_fields_uses_salesforce_aliases() -> None:
    fields = query_fields().split(", ")
    assert "Id" in fields
    assert "MailingPostalCode" in fields
    assert "Metro_Area__c" in fields
    # Every field must resolve to its Salesforce alias, not the Python attribute name.
    assert "zipcode" not in fields


@pytest.mark.parametrize(
    "arg",
    [
        "example.my.salesforce.com",
        "https://example.my.salesforce.com",
        "https://example.my.salesforce.com/",
        " example.my ",
    ],
)
def test_normalize_domain(arg: str) -> None:
    assert normalize_domain(arg) == "example.my"


@pytest.mark.parametrize(
    "arg", ["login.salesforce.com", "test.salesforce.com", "login", "", "example"]
)
def test_normalize_domain_rejects_generic_hosts(arg: str) -> None:
    with pytest.raises(ValueError):
        normalize_domain(arg)
