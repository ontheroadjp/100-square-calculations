"""Unit tests for nuts_calc_tex.py's pluggable LatexEngineAdapter interface
and NUTS_CALC_TEX_ENGINE selection (issue #120).

These exercise the pure-Python adapter-selection logic directly (no
pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py (e.g. test_cli_fails_clearly_when_pdflatex_missing,
which covers the CLI-level "binary not found" path for the default
adapter).
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_default_engine_name_is_pdflatex_when_env_var_unset(monkeypatch) -> None:
    monkeypatch.delenv(tex_module.LATEX_ENGINE_ENV_VAR, raising=False)
    assert tex_module.get_latex_engine_name() == tex_module.DEFAULT_LATEX_ENGINE == "pdflatex"


def test_engine_name_resolves_from_env_var(monkeypatch) -> None:
    monkeypatch.setenv(tex_module.LATEX_ENGINE_ENV_VAR, "pdflatex")
    assert tex_module.get_latex_engine_name() == "pdflatex"


def test_unknown_engine_name_raises_value_error(monkeypatch) -> None:
    monkeypatch.setenv(tex_module.LATEX_ENGINE_ENV_VAR, "bogus")
    with pytest.raises(ValueError, match="bogus"):
        tex_module.get_latex_engine_name()


def test_get_latex_engine_adapter_returns_pdflatex_adapter_by_default(monkeypatch) -> None:
    monkeypatch.delenv(tex_module.LATEX_ENGINE_ENV_VAR, raising=False)
    adapter = tex_module.get_latex_engine_adapter()
    assert isinstance(adapter, tex_module.PdflatexEngineAdapter)
    assert adapter.binary_name == "pdflatex"


def test_pdflatex_adapter_contributes_no_preamble_additions() -> None:
    assert tex_module.PdflatexEngineAdapter().build_preamble_additions() == ""


def test_build_preamble_tex_defaults_to_pdflatex_adapter_output() -> None:
    # No-adapter call must match an explicit PdflatexEngineAdapter() call,
    # so existing callers (and this file's own end-to-end CLI tests) that
    # never pass an adapter keep getting byte-identical output.
    default_tex = tex_module.build_preamble_tex("A4")
    explicit_tex = tex_module.build_preamble_tex("A4", tex_module.PdflatexEngineAdapter())
    assert default_tex == explicit_tex


def test_build_preamble_tex_splices_in_engine_preamble_additions() -> None:
    class StubEngineAdapter:
        binary_name = "stub"

        def build_preamble_additions(self) -> str:
            return "\\usepackage{stubpackage}\n"

        def compile(self, tex_source: str, out_pdf_path: str) -> None:
            raise NotImplementedError

    tex = tex_module.build_preamble_tex("A4", StubEngineAdapter())
    assert "\\usepackage{stubpackage}\n\\pagestyle{fancy}" in tex


def test_engine_name_resolves_lualatex_from_env_var(monkeypatch) -> None:
    monkeypatch.setenv(tex_module.LATEX_ENGINE_ENV_VAR, "lualatex")
    assert tex_module.get_latex_engine_name() == "lualatex"


def test_get_latex_engine_adapter_returns_lualatex_adapter_when_selected(monkeypatch) -> None:
    monkeypatch.setenv(tex_module.LATEX_ENGINE_ENV_VAR, "lualatex")
    adapter = tex_module.get_latex_engine_adapter()
    assert isinstance(adapter, tex_module.LuaLatexEngineAdapter)
    assert adapter.binary_name == "lualatex"


def test_lualatex_adapter_preamble_loads_fontspec_and_cjk_font() -> None:
    additions = tex_module.LuaLatexEngineAdapter().build_preamble_additions()
    assert "\\usepackage{fontspec}" in additions
    assert f"\\setmainfont{{{tex_module.LUALATEX_CJK_FONT_NAME}}}" in additions


def test_build_preamble_tex_splices_in_lualatex_adapter_preamble() -> None:
    tex = tex_module.build_preamble_tex("A4", tex_module.LuaLatexEngineAdapter())
    assert "\\usepackage{fontspec}\n\\setmainfont{Noto Sans CJK JP}\n\\pagestyle{fancy}" in tex
