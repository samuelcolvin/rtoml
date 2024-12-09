.DEFAULT_GOAL := all

.PHONY: .uv  # Check that uv is installed
.uv:
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit  # Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install  # Install the package, dependencies, and pre-commit for local development
install: .uv .pre-commit
	uv sync --frozen --group lint
	pre-commit install --install-hooks

.PHONY: sync  # Update local packages and uv.lock
sync: .uv
	uv sync --all-extras --all-packages --group lint --group docs

.PHONY: build-dev
build-dev:
	uv run maturin develop --uv

.PHONY: build-prod
build-prod:
	uv run maturin develop --release --uv

.PHONY: format
format:
	uv run ruff format
	uv run ruff check --fix --fix-only
	cargo fmt

.PHONY: lint-python
lint-python:
	uv run ruff format --check
	uv run ruff check

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings -A incomplete_features -W clippy::dbg_macro -W clippy::print_stdout

.PHONY: lint
lint: lint-python lint-rust

.PHONY: mypy
typecheck:
	uv run mypy python

.PHONY: test
test:
	uv run coverage run -m pytest

.PHONY: testcov
testcov: build-dev test
	@echo "building coverage html"
	@uv run coverage html

.PHONY: all
all: lint typecheck testcov
