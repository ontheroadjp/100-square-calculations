"""Unit tests for backend/app.py's Flask routes.

Uses Flask's test client (no running server, no subprocess execution) so
these run without a live backend or pdflatex.
"""

import importlib
import os
import subprocess
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


def test_renderer_info_defaults_to_latex_when_env_unset(client, monkeypatch) -> None:
    monkeypatch.delenv(renderers.RENDERER_ENV_VAR, raising=False)
    response = client.get("/renderer-info")
    assert response.status_code == 200
    assert response.get_json() == {"renderer": "latex"}


def test_renderer_info_rejects_removed_reportlab(client, monkeypatch) -> None:
    # nuts_calc.py/reportlab was removed (issue #232); explicit reportlab
    # is no longer a special case, just another unknown value.
    monkeypatch.setenv(renderers.RENDERER_ENV_VAR, "reportlab")
    response = client.get("/renderer-info")
    assert response.status_code == 500
    assert "Unknown NUTS_CALC_RENDERER value" in response.get_json()["error"]


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


def test_generate_pdf_com_requires_a_value(client) -> None:
    response = client.post("/generate-pdf", json={"paper_size": "A4", "command_type": "com"})
    assert response.status_code == 500
    assert "a_value (complement target) is required" in response.get_json()["error"]


def test_generate_pdf_com_rejects_a_value_below_minimum(client) -> None:
    backend_app = sys.modules["app"]
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "com", "a_value": backend_app.nuts_calc_tex.MIN_COMPLEMENT_TARGET - 1},
    )
    assert response.status_code == 500
    assert "must be at least" in response.get_json()["error"]


def test_generate_pdf_com_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The 'com' command_type must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #199), not via
    renderers.run's subprocess path -- assert this by making
    renderers.run raise if called, and by stubbing the LaTeX engine's
    compile() (no real pdflatex/lualatex needed) to write a dummy PDF.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'com'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "com", "a_value": 10}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_com_maps_compile_failure_to_500(client, monkeypatch) -> None:
    """
    engine_adapter.compile() calls nuts_calc_tex.failure() (print + exit(1),
    i.e. SystemExit) rather than raising a normal exception on a LaTeX
    compile error; the route must catch that and return a JSON 500 instead
    of letting the request thread die (issue #199 integration finding).
    """
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "com", "a_value": 10}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_other_command_types_still_use_subprocess_renderer(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fake_run(data, output_dir, renderer_name):
        pdf_path = os.path.join(output_dir, "worksheet_fake.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return pdf_path, "worksheet_fake.pdf", completed

    monkeypatch.setattr(backend_app.renderers, "run", fake_run)
    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "ope", "a_min": 1, "a_max": 9}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
