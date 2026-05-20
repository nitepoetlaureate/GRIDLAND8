.PHONY: setup test backend frontend docker clean install-hooks

PYTHON ?= python3
PIP    ?= pip

setup: install-hooks
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	npm install

install-hooks:
	bash scripts/install-hooks.sh

test:
	. .venv/bin/activate && PYTHONPATH=src pytest -q

backend:
	. .venv/bin/activate && PYTHONPATH=src uvicorn backend.main:app --reload --port 8000

frontend:
	npm run dev

docker:
	docker compose up --build

clean:
	rm -rf .venv node_modules dist .pytest_cache **/__pycache__
