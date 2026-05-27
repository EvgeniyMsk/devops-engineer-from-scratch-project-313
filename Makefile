install:
	uv sync

run:
	uv run python main.py

lint:
	uv run ruff check main.py paas_web_app

build:
	uv build

package-install: build
	uv tool install --reinstall ./dist/devops_engineer_from_scratch_project_313-0.1.0-py3-none-any.whl