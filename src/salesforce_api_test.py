from salesforce_api import query_fields


def test_query_fields_uses_salesforce_aliases() -> None:
    fields = query_fields().split(", ")
    assert "Id" in fields
    assert "MailingPostalCode" in fields
    assert "Metro_Area__c" in fields
    # Every field must resolve to its Salesforce alias, not the Python attribute name.
    assert "zipcode" not in fields
