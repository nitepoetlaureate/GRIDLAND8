.PHONY: setup test backend stop-backend frontend docker clean install-hooks

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

# Free port 8000 when a previous uvicorn/python backend is still running.
stop-backend:
	@pid=$$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null); \
	if [ -n "$$pid" ]; then \
		echo "Stopping process(es) on port 8000: $$pid"; \
		kill $$pid 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$pid 2>/dev/null || true; \
	else \
		echo "No listener on port 8000"; \
	fi

frontend:
	npm run dev

docker:
	docker compose up --build

clean:
	rm -rf .venv node_modules dist .pytest_cache **/__pycache__
