default:
    @just --list

install:
    uv sync

fmt:
    uv run ruff format

lint:
    uv run ruff format --check
    uv run ruff check
    uv run ty check

test:
    uv run pytest src

run *ARGS:
    PYTHONPATH=src uv run python src/main.py {{ARGS}}
