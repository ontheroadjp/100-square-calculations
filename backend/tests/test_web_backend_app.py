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


@pytest.mark.parametrize(
    "variant_fields",
    [
        {"vertical": True},
        {"intermediate": True},
        {"missing_value": True},
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
    format pattern 1a) is migrated by this issue (#205); every variant flag
    that selects a different pattern (vertical/intermediate) or an invalid
    use_parentheses combination must keep using the subprocess path. Plain
    use_parentheses (no other variant flag) is covered separately below
    (#206), and the terms family (terms/terms_min/terms_max/mixed_operators
    without use_parentheses) is covered separately below (#207): both now
    use the presentation API.
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
