.PHONY: install test lint typecheck verify demo build

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check src tests

typecheck:
	mypy src/agent_reliability_lab

verify: lint typecheck
	python -m pytest --cov=agent_reliability_lab --cov-branch --cov-report=term-missing

demo:
	python -m agent_reliability_lab suite scenarios --strategies baseline,resilient --output demo

build:
	python -m build

