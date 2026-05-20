"""Test configuration.

- Puts src/ on sys.path so `import backend` works without an install step.
- Provides a synchronous TestClient against the FastAPI app.
- Resets cached settings between tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def app():
    from backend.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)
