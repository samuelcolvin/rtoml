.DEFAULT_GOAL := all
isort = isort rtoml tests
black = black rtoml tests

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
	@rm -f rtoml/*.so
	cargo build
	@rm -f target/debug/lib_rtoml.d
	@rm -f target/debug/lib_rtoml.rlib
	@mv target/debug/lib_rtoml.* rtoml/_rtoml.so

.PHONY: build-prod
build-prod:
	@rm -f rtoml/*.so
	cargo build --release
	@rm -f target/release/lib_rtoml.d
	@rm -f target/release/lib_rtoml.rlib
	@mv target/release/lib_rtoml.* rtoml/_rtoml.so

.PHONY: format
format:
	$(isort)
	$(black)
	cargo fmt


.PHONY: lint-python
lint-python:
	ruff src tests
	$(isort) --check-only --df
	$(black) --check --diff

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
	pytest --cov=rtoml

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
