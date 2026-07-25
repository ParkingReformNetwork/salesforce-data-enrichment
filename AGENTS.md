# AGENTS.md

A simple Python project that runs in a cron job every day via GitHub Actions pipeline to improve the location information of contacts. It uses:

* Salesforce API: source of truth for contacts; reads and writes records.
* Mailchimp API: source of lat/long coordinates per email.
* OpenStreetMap's Nominatim API (via `geopy`): reverse-geocodes coordinates into addresses. Rate-limited per OSM's usage policy.
* `uszipcode`: local SQLite dataset for zip code lookups (not a live API).
* The https://ziptometro.com dataset: shipped as encrypted CSVs in `data/`, decrypted at runtime with `ENCRYPTION_KEY` in `src/metro_csvs.py`.

The pipeline works best with U.S.-based addresses, but it still attempts to enrich non-U.S. adddresses.

## How to run commands

* `just fmt`: autoformat
* `just lint`: run Ruff and ty (type checker)
* `just test`: run Pytest

## Coding style

* Keep code simple and maintainable. Use best practices like testing code, type hints, and a functional style (but not dogmatic). Avoid premature generalization.
* Tests should focus on our own code, rather than testing the std lib and third-parties other than our integration with them.
* Never leak personal information (PI) in logs and exceptions. Keep in mind the GitHub Actions logs are public.
* Keep in mind that we're using external APIs that can be rate limited. Where possible, avoid making unnecessary calls, consider retries, etc.
