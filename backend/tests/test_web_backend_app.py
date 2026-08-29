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


def test_generate_problems_hundred_square_returns_table_envelope(client) -> None:
    response = client.post(
        "/generate-problems", json={"paper_size": "A4", "command_type": "100", "num": 1}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "table" in body
    assert "problems" not in body
    table = body["table"]
    left_values = table["left_values"]
    top_values = table["top_values"]
    answers = table["answers"]
    assert len(left_values) == 10
    assert len(top_values) == 10
    assert len(answers) == 10
    for r in range(10):
        assert len(answers[r]) == 10
        for c in range(10):
            assert answers[r][c] == left_values[r] + top_values[c]


def test_generate_problems_hundred_square_still_requires_num(client) -> None:
    response = client.post(
        "/generate-problems", json={"paper_size": "A4", "command_type": "100"}
    )
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


def test_generate_pdf_kuku_requires_a_value(client) -> None:
    response = client.post("/generate-pdf", json={"paper_size": "A4", "command_type": "99"})
    assert response.status_code == 500
    assert "a_value (times-table row) is required" in response.get_json()["error"]


def test_generate_pdf_kuku_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The '99' command_type must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #208), not via
    renderers.run's subprocess path -- assert this the same way
    test_generate_pdf_com_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type '99'")

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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "99", "a_value": 7}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_abc_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'aBc'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\Rightarrow" in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "aBc"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_abc_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "aBc"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_kuku_forwards_descend_and_shuffle(client, monkeypatch) -> None:
    """
    frontend/web's g2-kuku preset (drillPresets.js) sends descend/shuffle for
    its descending/random question-order settings; the internal API path
    must forward them to generate_kuku_problems instead of silently falling
    back to ascending/non-shuffled order.
    """
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    captured = {}
    original_generate_kuku_problems = backend_app.nuts_calc_tex.generate_kuku_problems

    def spy_generate_kuku_problems(a_value, order, start_index, descend, shuffle):
        captured["descend"] = descend
        captured["shuffle"] = shuffle
        return original_generate_kuku_problems(a_value, order, start_index, descend, shuffle)

    monkeypatch.setattr(backend_app.nuts_calc_tex, "generate_kuku_problems", spy_generate_kuku_problems)

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
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "99", "a_value": 7, "descend": True, "shuffle": True},
    )
    assert response.status_code == 200
    assert captured == {"descend": True, "shuffle": True}


def test_generate_pdf_kuku_maps_compile_failure_to_500(client, monkeypatch) -> None:
    """
    engine_adapter.compile() calls nuts_calc_tex.failure() (print + exit(1),
    i.e. SystemExit) rather than raising a normal exception on a LaTeX
    compile error; the route must catch that and return a JSON 500 instead
    of letting the request thread die (mirrors #199's integration finding
    for 'com').
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "99", "a_value": 7}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_pi_requires_a_value(client) -> None:
    response = client.post("/generate-pdf", json={"paper_size": "A4", "command_type": "pi"})
    assert response.status_code == 500
    assert "a_value (starting multiplicand) is required" in response.get_json()["error"]


def test_generate_pdf_pi_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The 'pi' command_type must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #210), not via
    renderers.run's subprocess path -- assert this the same way as the
    'com' equivalent above.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'pi'")

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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "pi", "a_value": 5}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_pi_maps_compile_failure_to_500(client, monkeypatch) -> None:
    """
    engine_adapter.compile() calls nuts_calc_tex.failure() (print + exit(1),
    i.e. SystemExit) rather than raising a normal exception on a LaTeX
    compile error; the route must catch that and return a JSON 500 instead
    of letting the request thread die (issue #199 integration finding,
    also applicable to 'pi' since #210 reuses the same in-process compile
    path).
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "pi", "a_value": 5}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_squ_requires_a_value(client) -> None:
    response = client.post("/generate-pdf", json={"paper_size": "A4", "command_type": "squ"})
    assert response.status_code == 500
    assert "a_value (starting square number) is required" in response.get_json()["error"]


def test_generate_pdf_squ_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The 'squ' command_type must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #209), not via
    renderers.run's subprocess path -- assert this the same way
    test_generate_pdf_com_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'squ'")

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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "squ", "a_value": 3}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_squ_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "squ", "a_value": 3}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_lcm_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The 'lcm' command_type must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #211), not via
    renderers.run's subprocess path -- assert this by making
    renderers.run raise if called, and by stubbing the LaTeX engine's
    compile() (no real pdflatex/lualatex needed) to write a dummy PDF.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'lcm'")

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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "lcm"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_lcm_maps_compile_failure_to_500(client, monkeypatch) -> None:
    """
    engine_adapter.compile() calls nuts_calc_tex.failure() (print + exit(1),
    i.e. SystemExit) rather than raising a normal exception on a LaTeX
    compile error; the route must catch that and return a JSON 500 instead
    of letting the request thread die (mirrors the 'com' finding from #199).
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "lcm"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_divfrac_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'divfrac'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\div" in tex_source
        assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "divfrac"}
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_divfrac_resolves_digit_and_explicit_ranges(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured = {}
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def spy_generate_divfrac_problems(nums_a, nums_b, order, start_index):
        captured.update(
            nums_a=nums_a, nums_b=nums_b, order=order, start_index=start_index
        )
        return [backend_app.nuts_calc_tex.DivFracProblem(index=1, a=10, b=3)]

    def fake_compile(self, tex_source, out_pdf_path):
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex, "generate_divfrac_problems", spy_generate_divfrac_problems
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "divfrac",
            "a_digits": 2, "a_min": 7, "a_max": 8,
            "b_min": 3, "b_max": 4, "rows": 1, "columns": 1,
        },
    )

    assert response.status_code == 200
    assert captured == {
        "nums_a": list(range(10, 100)), "nums_b": [3, 4],
        "order": 1, "start_index": 1,
    }


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"b_min": 0}, "b_min must be at least 1"),
        ({"rows": 0}, "rows and columns must be at least"),
        ({"columns": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_divfrac_rejects_invalid_layout_or_denominator_range(
    client, request_fields, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "divfrac", **request_fields},
    )

    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_divfrac_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "divfrac"}
    )

    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_gcd_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    The 'gcd' command_type must build its PDF via the internal presentation
    API (issue #212), not via renderers.run's subprocess path.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'gcd'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\mathrm{GCD}" in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "gcd"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_gcd_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "gcd"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_evenodd_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'evenodd'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\Rightarrow" in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "evenodd"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_evenodd_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "evenodd"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_multiples_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'multiples'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    captured = {}
    original_generate = backend_app.nuts_calc_tex.generate_multiples_problems

    def spy_generate(nums_a, order, start_index, count):
        captured["count"] = count
        return original_generate(nums_a, order, start_index, count)

    monkeypatch.setattr(backend_app.nuts_calc_tex, "generate_multiples_problems", spy_generate)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\Rightarrow" in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "multiples", "multiples_count": 6},
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert captured == {"count": 6}


@pytest.mark.parametrize(
    ("field", "value", "error_text"),
    [
        ("a_min", 0, "a_min must be at least 1"),
        ("multiples_count", 0, "multiples_count must be at least"),
        ("rows", 0, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_multiples_rejects_invalid_basic_input(
    client, field, value, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "multiples", field: value},
    )
    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_multiples_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "multiples"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_divisors_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'divisors'")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    captured = {}
    original_generate = backend_app.nuts_calc_tex.generate_divisors_problems

    def spy_generate(nums_a, order, start_index):
        captured["nums_a"] = nums_a
        captured["order"] = order
        return original_generate(nums_a, order, start_index)

    monkeypatch.setattr(backend_app.nuts_calc_tex, "generate_divisors_problems", spy_generate)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\Rightarrow" in tex_source
        assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={
            "paper_size": "A4",
            "command_type": "divisors",
            "a_min": 10,
            "a_max": 12,
            "rows": 2,
            "columns": 3,
        },
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert captured == {"nums_a": [10, 11, 12], "order": 6}


@pytest.mark.parametrize(
    ("field", "value", "error_text"),
    [
        ("a_min", 0, "a_min must be at least 1"),
        ("rows", 0, "rows and columns must be at least"),
        ("columns", 0, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_divisors_rejects_invalid_basic_input(
    client, field, value, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "divisors", field: value},
    )
    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_divisors_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "divisors"}
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "100"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_frac_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'frac'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "frac", "rows": 1, "columns": 1}
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert "\\displaystyle \\frac" in captured_tex[0]
    assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in captured_tex[0]


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"numerator_digits": 0}, "numerator_digits must be between"),
        ({"same_denominator": True, "different_denominators": True}, "cannot be combined"),
        ({"rows": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_frac_rejects_invalid_basic_input(
    client, monkeypatch, request_fields, error_text
) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "frac", **request_fields},
    )
    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_frac_maps_compile_failure_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the fraction worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "frac", "rows": 1, "columns": 1}
    )

    assert response.status_code == 500
    assert "lualatex failed while building the fraction worksheet" in response.get_json()["error"]


def test_generate_pdf_simplify_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'simplify'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "simplify", "rows": 1, "columns": 1},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert "\\displaystyle \\frac" in captured_tex[0]
    assert "\\Rightarrow" in captured_tex[0]
    assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in captured_tex[0]


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"numerator_digits": 0}, "numerator_digits must be between"),
        ({"denominator_digits": 4}, "denominator_digits must be between"),
        ({"rows": 0}, "rows and columns must be at least"),
        ({"columns": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_simplify_rejects_invalid_basic_input(
    client, request_fields, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "simplify", **request_fields},
    )

    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_simplify_maps_compile_failure_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the simplify worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "simplify", "rows": 1, "columns": 1},
    )

    assert response.status_code == 500
    assert "lualatex failed while building the simplify worksheet" in response.get_json()["error"]


def test_generate_pdf_frac2dec_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'frac2dec'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "frac2dec"},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert "\\displaystyle \\frac" in captured_tex[0]
    assert "\\Rightarrow" in captured_tex[0]
    assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in captured_tex[0]


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"numerator_digits": 0}, "numerator_digits must be between"),
        ({"denominator_digits": 4}, "denominator_digits must be between"),
        ({"rows": 0}, "rows and columns must be at least"),
        ({"columns": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_frac2dec_rejects_invalid_basic_input(
    client, request_fields, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "frac2dec", **request_fields},
    )

    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_frac2dec_maps_compile_failure_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the frac2dec worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "frac2dec", "rows": 1, "columns": 1},
    )

    assert response.status_code == 500
    assert "lualatex failed while building the frac2dec worksheet" in response.get_json()["error"]


def test_generate_pdf_dec2frac_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'dec2frac'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "dec2frac"},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert "\\Rightarrow" in captured_tex[0]
    assert "\\displaystyle" in captured_tex[0]
    assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in captured_tex[0]


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"rows": 0}, "rows and columns must be at least"),
        ({"columns": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_dec2frac_rejects_invalid_basic_input(
    client, request_fields, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "dec2frac", **request_fields},
    )

    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_dec2frac_maps_compile_failure_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the dec2frac worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "dec2frac", "rows": 1, "columns": 1},
    )

    assert response.status_code == 500
    assert "lualatex failed while building the dec2frac worksheet" in response.get_json()["error"]


def test_generate_pdf_commondenom_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type 'commondenom'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "commondenom"},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert "\\Rightarrow" in captured_tex[0]
    assert "\\displaystyle" in captured_tex[0]
    assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in captured_tex[0]


@pytest.mark.parametrize(
    ("request_fields", "error_text"),
    [
        ({"rows": 0}, "rows and columns must be at least"),
        ({"columns": 0}, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_commondenom_rejects_invalid_basic_input(
    client, request_fields, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "commondenom", **request_fields},
    )

    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_commondenom_maps_compile_failure_to_500(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def failing_compile(self, tex_source, out_pdf_path):
        backend_app.nuts_calc_tex.failure("lualatex failed while building the commondenom worksheet")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", failing_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", failing_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "commondenom", "rows": 1, "columns": 1},
    )

    assert response.status_code == 500
    assert "lualatex failed while building the commondenom worksheet" in response.get_json()["error"]


def test_generate_pdf_mixed_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for a basic mixed request")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)

    def fake_compile(self, tex_source, out_pdf_path):
        assert "\\displaystyle" in tex_source
        assert backend_app.nuts_calc_tex.BLANK_ANSWER_TEX in tex_source
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "mixed"}
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


@pytest.mark.parametrize(
    "variant_fields",
    [
        {"terms": 3},
        {"terms_min": 2, "terms_max": 4},
        {"mixed_operators": True},
        {"reducible_mode": "required"},
    ],
)
def test_generate_pdf_mixed_variants_still_use_subprocess_renderer(
    client, monkeypatch, variant_fields
) -> None:
    backend_app = sys.modules["app"]

    def fake_run(data, output_dir, renderer_name):
        pdf_path = os.path.join(output_dir, "worksheet_fake.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return pdf_path, "worksheet_fake.pdf", completed

    monkeypatch.setattr(backend_app.renderers, "run", fake_run)
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "mixed", **variant_fields},
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


@pytest.mark.parametrize(
    ("field", "value", "error_text"),
    [
        ("numerator_digits", 0, "numerator_digits must be between"),
        ("denominator_digits", 4, "denominator_digits must be between"),
        ("decimal_places", 3, "decimal_places must be between"),
        ("a_kind", ["bogus"], "a_kind and b_kind must contain only"),
        ("operator", ["bogus"], "operator must contain only"),
        ("rows", 0, "rows and columns must be at least"),
    ],
)
def test_generate_pdf_mixed_rejects_invalid_basic_input(
    client, field, value, error_text
) -> None:
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "mixed", field: value},
    )
    assert response.status_code == 500
    assert error_text in response.get_json()["error"]


def test_generate_pdf_mixed_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "mixed"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


@pytest.mark.parametrize(
    "variant_fields",
    [
        {"vertical": True},
        {"intermediate": True},
        # use_parentheses combined with a mutually-exclusive flag (invalid
        # per nuts_calc_tex.py's _init() validation, nuts_calc_tex.py:
        # 676-692) must NOT be picked up by _is_tree_ope_pdf_request either;
        # it falls back to the subprocess path like every other rejected
        # combination.
        {"use_parentheses": True, "vertical": True},
        {"use_parentheses": True, "intermediate": True},
        {"use_parentheses": True, "missing_value": True},
    ],
)
def test_generate_pdf_ope_variants_still_use_subprocess_renderer(client, monkeypatch, variant_fields) -> None:
    """
    Only the plain 2-term 'ope' shape (build_horizontal_block_tex, content-
    format pattern 1a) is migrated by #205; every variant flag that selects
    a still-unmigrated pattern (vertical/intermediate) or an invalid
    use_parentheses combination must keep using the subprocess path. Plain
    use_parentheses (no other variant flag) is covered separately below
    (#206), the terms family (terms/terms_min/terms_max/mixed_operators
    without use_parentheses) below (#207), and missing_value below (#223):
    each now uses the presentation API. Only an invalid use_parentheses +
    missing_value combination stays on the subprocess path here.
    """
    backend_app = sys.modules["app"]

    def fake_run(data, output_dir, renderer_name):
        pdf_path = os.path.join(output_dir, "worksheet_fake.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return pdf_path, "worksheet_fake.pdf", completed

    monkeypatch.setattr(backend_app.renderers, "run", fake_run)
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "ope", "a_min": 1, "a_max": 9, **variant_fields},
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    A plain 2-term 'ope' request must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #205), not via
    renderers.run's subprocess path -- assert this the same way
    test_generate_pdf_com_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for a plain 2-term 'ope' request")

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
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "ope", "a_min": 1, "a_max": 9, "operator": ["add"]},
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "ope", "a_min": 1, "a_max": 9}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_ope_tree_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    An `ope --use-parentheses` (tree variant) request must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #206), not via
    renderers.run's subprocess path -- assert this the same way
    test_generate_pdf_ope_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for an ope --use-parentheses request")

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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "use_parentheses": True,
            "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9, "operator": ["add"],
        },
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_tree_supports_terms_family_via_presentation_api(client, monkeypatch) -> None:
    """
    The terms family (terms/terms_min/terms_max/mixed_operators) is
    --use-parentheses's own N-term generalization (issue #71), not a
    separate not-yet-migrated variant -- it must also route through the
    presentation API, not fall back to the subprocess path.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for an ope --use-parentheses + terms request")

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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "use_parentheses": True,
            "terms_min": 3, "terms_max": 4, "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
        },
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_tree_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "use_parentheses": True,
            "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
        },
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


@pytest.mark.parametrize(
    "variant_fields",
    [
        {"terms": 3},
        {"terms_min": 2, "terms_max": 4},
        {"mixed_operators": True},
    ],
)
def test_generate_pdf_ope_multi_term_uses_presentation_api_not_subprocess(client, monkeypatch, variant_fields) -> None:
    """
    A flat multi-term 'ope' request (terms family, no use_parentheses) must
    build its PDF via nuts_calc_tex.build_presentation_document_tex (issue
    #207), not via renderers.run's subprocess path -- assert this the same
    way test_generate_pdf_ope_tree_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for a multi-term ope request")

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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope",
            "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9, "operator": ["add"],
            **variant_fields,
        },
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_multi_term_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "terms": 3,
            "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
        },
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_ope_missing_value_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """
    An `ope --missing-value` (mushikuizan) request must build its PDF via
    nuts_calc_tex.build_presentation_document_tex (issue #223), not via
    renderers.run's subprocess path -- assert this the same way
    test_generate_pdf_ope_uses_presentation_api_not_subprocess does.
    """
    backend_app = sys.modules["app"]

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for an 'ope --missing-value' request")

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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "missing_value": True,
            "a_min": 1, "a_max": 9, "operator": ["add"],
        },
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_generate_pdf_ope_missing_value_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf",
        json={
            "paper_size": "A4", "command_type": "ope", "missing_value": True,
            "a_min": 1, "a_max": 9,
        },
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_hundred_square_uses_presentation_api_not_subprocess(client, monkeypatch) -> None:
    """The '100' command_type must build its PDF via the internal
    presentation API (issue #229), not renderers.run's subprocess path, and
    without a per-problem number box (single unnumbered full-area slot)."""
    backend_app = sys.modules["app"]
    captured_tex = []

    def fail_if_called(*args, **kwargs):
        raise AssertionError("renderers.run must not be called for command_type '100'")

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.renderers, "run", fail_if_called)
    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        backend_app.nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "100"},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert len(captured_tex) == 1
    assert f"\\rowcolor{{{backend_app.nuts_calc_tex.HUNDRED_SQUARE_HEADER_COLOR}}}" in captured_tex[0]
    assert "\\makebox[" not in captured_tex[0]


def test_generate_pdf_hundred_square_matches_legacy_document_output(client, monkeypatch) -> None:
    """Issue #229 Done Criteria: existing visual output is preserved as-is.
    The presentation-API TeX for one blank table must be byte-identical to
    the legacy build_document_tex path for the same table."""
    backend_app = sys.modules["app"]
    tex_module = backend_app.nuts_calc_tex
    captured_tex = []

    table = tex_module.HundredSquareTable(
        left_values=list(range(1, 11)), top_values=list(range(1, 11))
    )

    def fake_generate_hundred_square(nums_left, nums_top):
        return table

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(backend_app.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name)
    monkeypatch.setattr(
        backend_app.nuts_calc_tex, "generate_hundred_square", fake_generate_hundred_square
    )
    monkeypatch.setattr(
        tex_module.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        tex_module.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )

    response = client.post(
        "/generate-pdf", json={"paper_size": "A4", "command_type": "100"}
    )
    assert response.status_code == 200

    engine_adapter = tex_module.get_latex_engine_adapter()
    blank_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=False)],
        columns=1,
        layout="block",
    )
    filled_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=True)],
        columns=1,
        layout="block",
    )
    legacy_tex = tex_module.build_document_tex(
        "A4", [blank_page], [filled_page], "blank", engine_adapter
    )

    assert captured_tex[0] == legacy_tex


def test_generate_pdf_hundred_square_maps_compile_failure_to_500(client, monkeypatch) -> None:
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
        "/generate-pdf", json={"paper_size": "A4", "command_type": "100"}
    )
    assert response.status_code == 500
    assert "lualatex failed while building the worksheet" in response.get_json()["error"]


def test_generate_pdf_hundred_square_rejects_too_narrow_axis_range(client) -> None:
    """Shared with the /generate-problems `100` path: an axis range spanning
    fewer than the minimum distinct values is a 500 ValueError, not a crash."""
    response = client.post(
        "/generate-pdf",
        json={"paper_size": "A4", "command_type": "100", "a_min": 5, "a_max": 5},
    )
    assert response.status_code == 500
    assert "distinct values" in response.get_json()["error"]
