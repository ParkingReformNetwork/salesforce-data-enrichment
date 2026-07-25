# Salesforce data enrichment

A pipeline to improve the location information of contacts, such as adding a metropolitan area.

## How to use

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

You also must set the environment variables `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_TOKEN`, and `ENCRYPTION_KEY`. Consider using `direnv` and an `.envrc` file. Get `ENCRYPTION_KEY` from other project maintainers. The Salesforce variables require having a Salesforce account with access. You can get the Salesforce security token by going to Settings -> Personal Information -> Reset My Security Token.

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
