"""Unit tests for web/backend/app.py's Flask routes.

Uses Flask's test client (no running server, no subprocess execution) so
these run without a live backend or pdflatex.
"""

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "web" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import pytest

import renderers  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    # app.py's top-level `os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)` resolves
    # './generated_pdfs' relative to cwd; chdir to BACKEND_DIR before the
    # first import so it lands under web/backend/ (matching the documented
    # `cd web/backend && python app.py` run pattern) instead of the repo root.
    monkeypatch.chdir(BACKEND_DIR)
    backend_app = importlib.import_module("app")
    backend_app.app.testing = True
    return backend_app.app.test_client()


def test_renderer_info_defaults_to_reportlab_when_env_unset(client, monkeypatch) -> None:
    monkeypatch.delenv(renderers.RENDERER_ENV_VAR, raising=False)
    response = client.get("/renderer-info")
    assert response.status_code == 200
    assert response.get_json() == {"renderer": "reportlab"}


def test_renderer_info_reads_env_var(client, monkeypatch) -> None:
    monkeypatch.setenv(renderers.RENDERER_ENV_VAR, "latex")
    response = client.get("/renderer-info")
    assert response.status_code == 200
    assert response.get_json() == {"renderer": "latex"}


def test_renderer_info_rejects_unknown_renderer_env_value(client, monkeypatch) -> None:
    monkeypatch.setenv(renderers.RENDERER_ENV_VAR, "bogus")
    response = client.get("/renderer-info")
    assert response.status_code == 500
    assert "Unknown NUTS_CALC_RENDERER value" in response.get_json()["error"]
