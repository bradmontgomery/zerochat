SHELL := /bin/bash

.PHONY: clean_env
clean_env:
	rm -Rf .venv

.PHONY: build_env
build_env:
	uv venv
	@echo ""
	@echo "********** Run \`source .venv/bin/activate\` before continuing **********"
	@echo ""

.PHONY: rebuild_env
rebuild_env: | clean_env build_env

.PHONY: install
install:
	uv sync
	uv run pre-commit install

.PHONY: lock
lock:
	uv lock --upgrade
	uv run pre-commit autoupdate

.PHONY: build
build:
	uv build

.PHONY: test
test:
	uv run pytest

.PHONY: lint
lint:
	uv run black --check zerochat/
	uv run isort --check zerochat/
	uv run flake8 zerochat/

.PHONY: format
format:
	uv run black zerochat/
	uv run isort zerochat/

# TODO
#.PHONY: upload
#upload:
#	uv run twine upload dist/*