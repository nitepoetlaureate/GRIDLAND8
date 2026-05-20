.PHONY: setup test backend frontend docker clean

PYTHON ?= python3
PIP    ?= pip

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	npm install

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
