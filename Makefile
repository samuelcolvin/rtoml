.DEFAULT_GOAL := all

install:
	pip install -U pip wheel pre-commit
	pip install -r tests/requirements.txt
	pip install -e .
	pre-commit install

.PHONY: install-all
install-all: install
	pip install -r tests/requirements-linting.txt

.PHONY: build-dev
build-dev:
	maturin develop

.PHONY: build-prod
build-prod:
	maturin develop --release

.PHONY: format
format:
	ruff check --fix-only rtoml tests
	ruff format rtoml tests
	cargo fmt


.PHONY: lint-python
lint-python:
	ruff check rtoml tests
	ruff format --check rtoml tests

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings -A incomplete_features -W clippy::dbg_macro -W clippy::print_stdout

.PHONY: lint
lint: lint-python lint-rust

.PHONY: mypy
mypy:
	mypy rtoml

.PHONY: test
test:
	coverage run -m pytest

.PHONY: testcov
testcov: build test
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: lint mypy testcov

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf dist
	rm -rf build
	rm -rf target
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -f rtoml/*.so
	python setup.py clean
