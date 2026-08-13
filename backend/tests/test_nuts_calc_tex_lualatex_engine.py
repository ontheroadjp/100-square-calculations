"""End-to-end tests for the Japanese-capable LuaLaTeX engine adapter
(issue #121, building on the pluggable LatexEngineAdapter interface from
issue #120).

These are skipped when `lualatex` is not on PATH, mirroring the
`pdflatex`-gated tests in test_nuts_calc_tex.py. Pure-Python
adapter-selection/preamble tests (no lualatex required) live in
test_nuts_calc_tex_engine_adapter.py.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from nuts_calc_tex import (
    LuaLatexEngineAdapter,
    Page,
    build_document_tex,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
NUTS_CALC_TEX = BACKEND_DIR / "nuts_calc_tex.py"

CLI_TIMEOUT_SECONDS = 60

pytestmark = pytest.mark.skipif(
    shutil.which("lualatex") is None,
    reason="these tests require lualatex on PATH to exercise the Japanese-capable engine adapter",
)


def _assert_is_pdf(path: Path) -> None:
    assert path.exists(), f"expected PDF at {path}"
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


def test_lualatex_engine_compiles_japanese_text_without_crashing(tmp_path):
    page = Page(blocks=["1) $12 \\div 5 = 2 \\cdots$ あまり2 なまえ：\\underline{\\hspace{8cm}}"], columns=1)
    tex_source = build_document_tex(
        "A4", [page], [page], mode="blank", engine_adapter=LuaLatexEngineAdapter(),
    )
    assert "あまり2" in tex_source
    assert "なまえ：" in tex_source

    out_pdf = tmp_path / "japanese.pdf"
    LuaLatexEngineAdapter().compile(tex_source, str(out_pdf))

    _assert_is_pdf(out_pdf)


def test_cli_ope_vertical_produces_pdfs_under_lualatex_engine(tmp_path):
    env = os.environ.copy()
    env["NUTS_CALC_TEX_ENGINE"] = "lualatex"
    result = subprocess.run(
        [
            sys.executable, str(NUTS_CALC_TEX), "A4", "ope",
            "-o", "add", "sub", "mul", "div", "--vertical",
            "-r", "2", "-c", "2", "-p", "1", "--out-file", "vertical.pdf",
        ],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=CLI_TIMEOUT_SECONDS,
    )
    assert result.returncode == 0, result.stderr

    _assert_is_pdf(tmp_path / "vertical.pdf")
