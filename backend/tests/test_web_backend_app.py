"""Unit tests for backend/app.py's Flask routes.

Uses Flask's test client (no running server, no subprocess execution) so
these run without a live backend or pdflatex.
"""

import importlib
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest

import renderers  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    # app.py's top-level `os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)` resolves
    # './generated_pdfs' relative to cwd; chdir to BACKEND_DIR before the
    # first import so it lands under backend/ (matching the documented
    # `cd backend && python app.py` run pattern) instead of the repo root.
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


def test_generate_problems_returns_problems_from_the_data_layer(client, monkeypatch) -> None:
    monkeypatch.delenv(renderers.RENDERER_ENV_VAR, raising=False)
    backend_app = sys.modules["app"]
    monkeypatch.setattr(
        backend_app.problem_generation, "generate_problems",
        lambda data, renderer_name: [{"index": 1, "a": 2, "operator": "add", "b": 3, "result": 5}],
    )
    response = client.post("/generate-problems", json={"paper_size": "A4", "command_type": "ope", "num": 1})
    assert response.status_code == 200
    assert response.get_json() == {"problems": [{"index": 1, "a": 2, "operator": "add", "b": 3, "result": 5}]}


def test_generate_problems_requires_paper_size_and_command_type(client) -> None:
    response = client.post("/generate-problems", json={"num": 1})
    assert response.status_code == 400
    assert "Missing required parameters" in response.get_json()["error"]


@pytest.mark.parametrize("num", [0, -1, "5", None])
def test_generate_problems_rejects_invalid_num(client, num) -> None:
    body = {"paper_size": "A4", "command_type": "ope"}
    if num is not None:
        body["num"] = num
    response = client.post("/generate-problems", json=body)
    assert response.status_code == 400
    assert "num" in response.get_json()["error"]


def test_generate_problems_maps_data_layer_value_error_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def raise_value_error(data, renderer_name):
        raise ValueError("command_type 'frac' is not yet supported")

    monkeypatch.setattr(backend_app.problem_generation, "generate_problems", raise_value_error)
    response = client.post("/generate-problems", json={"paper_size": "A4", "command_type": "frac", "num": 1})
    assert response.status_code == 500
    assert "not yet supported" in response.get_json()["error"]
