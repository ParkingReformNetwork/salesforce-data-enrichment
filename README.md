# Salesforce data enrichment

A pipeline to improve the location information of contacts, such as adding a metropolitan area.

## How to use

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

You also must set the environment variables `SALESFORCE_CONSUMER_KEY`, `SALESFORCE_CONSUMER_SECRET`, `SALESFORCE_DOMAIN`, `ENCRYPTION_KEY`, `MAILCHIMP_KEY`, and `MAILCHIMP_LIST_ID`. Consider using `direnv` and an `.envrc` file. Get `ENCRYPTION_KEY` and the Mailchimp variables from other project maintainers.

The Salesforce variables come from an External Client App configured for the OAuth 2.0 client credentials flow (username/password login uses the SOAP `login()` call, which Salesforce is retiring). A Salesforce admin creates the app in Setup -> External Client Apps Manager, enables OAuth with the `api` scope and the client credentials flow, sets a dedicated integration user as the run-as user under Edit Policies, and shares the Consumer Key and Secret. `SALESFORCE_DOMAIN` is the org's My Domain (Setup -> My Domain), e.g. `example.my.salesforce.com`. The run-as user needs read on `Contact.Email` and read/edit on `MailingStreet`, `MailingCity`, `MailingState`, `MailingPostalCode`, `MailingCountry`, `MailingLatitude`, `MailingLongitude`, and `Metro_Area__c`.

### Install

```bash
just install
```

### Test

```bash
just test
```

### Format

```bash
just fmt
```

### Lint and typecheck

```bash
just lint
```

### Run script

```bash
just run
```

### Refresh the US zip code dataset

`data/us-zip-to-city-state.csv` stores zip → city/state and is used to fill in missing city and
state for US addresses. It is generated from [GeoNames' public postal code
dataset](https://download.geonames.org/export/zip/US.zip) (CC BY 4.0). The file is checked
into the repo rather than fetched at runtime. To pull a fresh copy:

```bash
uv run python scripts/refresh_us_zip_data.py
```
