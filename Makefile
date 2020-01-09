.DEFAULT_GOAL := all
isort = isort -rc rtoml tests
black = black -S -l 120 --target-version py36 rtoml tests

install:
	pip install -U pip wheel setuptools setuptools-rust
	pip install -U -r tests/requirements.txt

.PHONY: build
build:
	python ./setup.py develop

.PHONY: format
format:
	$(isort)
	$(black)
	cargo fmt

.PHONY: lint
lint:
	flake8 rtoml/ tests/
	$(isort) --check-only
	$(black) --check
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings

.PHONY: check-dist
check-dist:
	python setup.py check -ms
	python setup.py sdist
	twine check dist/*

.PHONY: mypy
mypy:
	mypy rtoml

.PHONY: test
test:
	pytest --cov=rtoml

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: testcov lint mypy

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
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
