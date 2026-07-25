import os
import sys

_REQUIRED_VARS = (
    "SALESFORCE_USERNAME",
    "SALESFORCE_PASSWORD",
    "SALESFORCE_TOKEN",
    "ENCRYPTION_KEY",
    "MAILCHIMP_KEY",
    "MAILCHIMP_LIST_ID",
)


def check_required_env_vars() -> None:
    """Exit early if any required secret is missing, before any API calls are made."""
    missing = [name for name in _REQUIRED_VARS if name not in os.environ]
    if missing:
        sys.exit(f"Missing required environment variables: {', '.join(missing)}")


def pop_env(*names: str) -> tuple[str, ...]:
    return tuple(os.environ.pop(name) for name in names)
