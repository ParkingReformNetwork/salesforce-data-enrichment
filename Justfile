default:
    @just --list

install:
    uv sync

fmt:
    uv run ruff format src

lint:
    uv run ruff check src

check:
    uv run mypy src

test:
    uv run pytest src

run *ARGS:
    PYTHONPATH=src uv run python src/main.py {{ARGS}}
