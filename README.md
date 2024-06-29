# Salesforce data enrichment

A pipeline to improve the location information of contacts, such as adding a metropolitan area.

## How to use

### Prerequisites

This uses [Pantsbuild](https://www.pantsbuild.org).

You also must set the environment variables `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_TOKEN`, and `ENCRYPTION_KEY`. Consider using `direnv` and an `.envrc` file. Get `ENCRYPTION_KEY` from other project maintainers. The Salesforce variables require having a Salesforce account with access. You can get the Salesforce security token by going to Settings -> Personal Information -> Reset My Security Token. 

### Test

```
pants test ::
```

### Format

```bash
pants fmt ::
```

### Run script

```bash
pants run src/main.py
```

### Update lockfile

```bash
pants generate-lockfiles --resolve=python-default
```