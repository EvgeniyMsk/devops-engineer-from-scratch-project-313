UV ?= uv
FRAMEWORK ?= flask

setup:
	UV_PYTHON_DOWNLOADS=never \
	UV_PYTHON_PREFERENCE=only-system \
	$(UV) sync --system

install:
	$(UV) sync

run:
	$(UV) run python main.py

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest

dev:
	@if [ "$(FRAMEWORK)" != "flask" ]; then \
		echo "Unsupported FRAMEWORK=$(FRAMEWORK). Supported: flask"; \
		exit 1; \
	fi
	npm install
	npm run dev

build:
	$(UV) build

package-install: build
	$(UV) tool install --reinstall ./dist/devops_engineer_from_scratch_project_313-0.1.0-py3-none-any.whl
