.PHONY: install test lint run serve improve

install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check src tests

run:
	docs-loop run "Improve the getting-started guide. State the Python requirement, add the pip installation command, and keep the link to the configuration guide. Make only the necessary documentation changes." --reset

serve:
	docs-loop serve --reload

improve:
	docs-loop improve --offline
