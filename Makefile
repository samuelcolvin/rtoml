.DEFAULT_GOAL := all
isort = isort rtoml tests
black = black -S -l 120 --target-version py38 rtoml tests

install:
	pip install -U pip wheel setuptools setuptools-rust
	pip install -U -r tests/requirements.txt

.PHONY: install-all
install-all: install
	pip install -r tests/requirements-linting.txt

.PHONY: build-dev
build-dev:
	python ./setup.py develop

.PHONY: build-prod
build-prod:
	python ./setup.py install

.PHONY: format
format:
	$(isort)
	$(black)
	cargo fmt

.PHONY: lint
lint:
	flake8 rtoml/ tests/
	$(isort) --check-only --df
	$(black) --check --diff
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings

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
