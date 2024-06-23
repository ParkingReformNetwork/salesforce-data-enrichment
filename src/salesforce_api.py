import os

from simple_salesforce import Salesforce

from salesforce_entry import SalesforceEntry


INSTANCE_URL = os.environ.pop("SALESFORCE_INSTANCE_URL")
TOKEN = os.environ.pop("SALESFORCE_TOKEN")
sf = Salesforce(instance_url=INSTANCE_URL, session_id=TOKEN)


def load_salesforce_data() -> list[SalesforceEntry]:
    fields = ", ".join(info.alias for info in SalesforceEntry.model_fields.values())
    return [
        SalesforceEntry(**raw)
        for raw in sf.query_all_iter(f"SELECT {fields} FROM Contact")
    ]
