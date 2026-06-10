# Convenience targets — canonical cross-platform path is Python scripts.
# Requires GNU Make. On Windows, prefer: python scripts/format_code.py etc.

.PHONY: format check test typecheck lint

format:
	python scripts/format_code.py

check:
	python scripts/check_project.py

test:
	python -m pytest

typecheck:
	python -m mypy iva main.py

lint:
	python -m ruff check .
