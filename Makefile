PYTHON ?= python3
MAIN = a_maze_ing.py
CONFIG = config.txt

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install flake8 mypy pytest build

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -path ./.venv -prune -o -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache build dist *.egg-info mazegen.egg-info

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

test:
	$(PYTHON) -m pytest

build:
	$(PYTHON) -m build
	cp dist/*.whl .

.PHONY: install run debug clean lint lint-strict test build