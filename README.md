# Salesforce data enrichment

A pipeline to improve the location information of contacts, such as adding a metropolitan area.

## How to use

### Prerequisites

This uses [Pantsbuild](https://www.pantsbuild.org).

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