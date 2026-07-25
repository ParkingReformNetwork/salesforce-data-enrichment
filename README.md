# Salesforce data enrichment

A pipeline to improve the location information of contacts, such as adding a metropolitan area.

## How to use

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

You also must set the environment variables `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_TOKEN`, `ENCRYPTION_KEY`, `MAILCHIMP_KEY`, and `MAILCHIMP_LIST_ID`. Consider using `direnv` and an `.envrc` file. Get `ENCRYPTION_KEY` and the Mailchimp variables from other project maintainers. The Salesforce variables require having a Salesforce account with access. You can get the Salesforce security token by going to Settings -> Personal Information -> Reset My Security Token.

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
