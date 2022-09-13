PY_VER ?= 3.10
SHELL := /bin/bash

.PHONY: clean_env
clean_env:
	rm -Rf ./env

.PHONY: build_env
build_env:
	python$(PY_VER) -m venv env
	@echo ""
	@echo "********** Run \`source env/bin/activate\` before continuing **********"
	@echo ""

.PHONY: rebuild_env
rebuild_env: | clean_env build_env

.PHONY: install
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install

.PHONY: compile
compile:
	pip install --upgrade pip pip-tools pre-commit
	pip-compile -rU  --no-emit-index-url -o requirements.txt requirements.in
	pre-commit autoupdate

.PHONY: build
build:
	python -m build

# TODO
#.PHONY: upload
#upload:
#	python -m twine upload dist/*