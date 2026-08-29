"""Tests for the shared "staged arrow-chain" content-format component
(taxonomy pattern 5) introduced by issue #268.

Issue #268 retrofits ``build_horizontal_intermediate_block_tex``
(``ope --intermediate``) so its three-stage ``a \\times b => <memo> => c``
body is emitted through the shared ``\\stagedchaineq`` wrapper, the
centralized ``\\stagechainarrow`` stage separator, and the fixed-width
``\\stagechainmemo`` box, instead of a raw ``$...$`` f-string that inlined
the two ``\\Rightarrow`` arrows with no explicit spacing.

- The ``\\times`` first stage reuses issue #264's centralized ``\\opspace``
  gap via ``build_equation_lhs_tex`` (same as ``squ`` / ``99``).
- The always-4-digit mental-math memo (still produced by
  ``build_intermediate_memo``) sits in a fixed-width centered box so the
  second arrow anchors at a constant x-offset on every problem.
- ``\\stagedchaineq`` adds ``\\vphantom{0}`` so a blank trailing result
  (a zero-height ``\\hspace``) keeps the same row height as an answer-key
  digit.

``ope --intermediate`` is not on the internal presentation API (it still
routes through the CLI / subprocess path), so the real-PDF spot checks
compile through the legacy ``build_document_tex`` builder. Each is skipped
when its engine binary is absent (mirroring
test_nuts_calc_tex_comparison_content_format.py).
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def _problem(index: int = 1, a: int = 23, b: int = 4, c: int = 92) -> "tex_module.OpeProblem":
    return tex_module.OpeProblem(index=index, a=a, b=b, operator="mul", c=c)


# --- shared macro block -----------------------------------------------------

def test_content_format_macros_define_the_staged_arrow_chain_components() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newlength{\\stagechaingapwidth}" in macros
    assert (
        f"\\setlength{{\\stagechaingapwidth}}{{{tex_module.CONTENT_FORMAT_STAGE_CHAIN_ARROW_GAP_TEX}}}"
        in macros
    )
    assert (
        "\\newcommand{\\stagechainarrow}{\\hspace{\\stagechaingapwidth}\\Rightarrow\\hspace{\\stagechaingapwidth}}"
        in macros
    )
    assert "\\newlength{\\stagechainmemowidth}" in macros
    assert (
        f"\\setlength{{\\stagechainmemowidth}}{{{tex_module.CONTENT_FORMAT_STAGE_CHAIN_MEMO_WIDTH_TEX}}}"
        in macros
    )
    assert (
        "\\newcommand{\\stagechainmemo}[1]{\\hbox to \\stagechainmemowidth{\\hfil\\ensuremath{#1}\\hfil}}"
        in macros
    )
    # \makebox[ is deliberately NOT used here: #229's layout tests assert its
    # absence as a proxy for "the problem-number box was skipped".
    assert "\\makebox[" not in macros
    assert "\\newcommand{\\stagedchaineq}[1]{$#1\\vphantom{0}$}" in macros


def test_content_format_macros_leave_the_pattern_1_2_3_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}" in macros
    assert "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}" in macros
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros
    assert "\\newcommand{\\compareeq}[1]{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}" in macros


def test_macros_are_spliced_into_the_legacy_document_builder() -> None:
    blank, filled = tex_module.build_ope_page_pair([_problem()], 1, False, True)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\stagedchaineq}" in document
    assert document.index("\\newcommand{\\stagedchaineq}") < document.index("\\begin{document}")


# --- staged-chain body helper ---------------------------------------------

def test_build_staged_chain_equation_tex_wraps_via_the_shared_components() -> None:
    body = tex_module.build_staged_chain_equation_tex(
        "23 \\opspace \\times \\opspace 4", "0812", "92"
    )
    assert body == (
        "\\stagedchaineq{23 \\opspace \\times \\opspace 4 \\stagechainarrow "
        "\\stagechainmemo{0812} \\stagechainarrow 92}"
    )


# --- block builder: blank vs filled -------------------------------------

def test_intermediate_block_blank_hides_answer_behind_the_fixed_blank_marker() -> None:
    problem = _problem(a=23, b=4, c=92)

    blank = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=False)
    filled = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=True)

    assert blank == (
        "1) \\stagedchaineq{23 \\opspace \\times \\opspace 4 \\stagechainarrow "
        "\\stagechainmemo{0812} \\stagechainarrow \\hspace{1.5em}}"
    )
    assert filled == (
        "1) \\stagedchaineq{23 \\opspace \\times \\opspace 4 \\stagechainarrow "
        "\\stagechainmemo{0812} \\stagechainarrow 92}"
    )
    assert "92" not in blank
    assert "\\underline" not in blank
    assert tex_module.BLANK_ANSWER_TEX in blank


def test_intermediate_block_times_operand_carries_the_centralized_opspace_gap() -> None:
    problem = _problem(index=7, a=48, b=6, c=288)

    filled = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=True)

    # the \times first stage is built by build_equation_lhs_tex, exactly like squ/99
    assert "48 \\opspace \\times \\opspace 6 \\stagechainarrow" in filled
    assert filled.startswith("7) \\stagedchaineq{")


def test_intermediate_block_memo_is_wrapped_in_the_fixed_width_box_from_build_intermediate_memo() -> None:
    problem = _problem(a=32, b=6, c=192)
    memo = tex_module.build_intermediate_memo(32, 6)

    assert memo == "1812"  # delegation unchanged
    block = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=True)
    assert f"\\stagechainmemo{{{memo}}}" in block


# --- real-PDF spot checks (both engines, blank + filled) --------------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("mode", ["blank", "filled"])
def test_intermediate_page_compiles_to_pdf(engine_name: str, mode: str, tmp_path: Path) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    problems = [
        tex_module.OpeProblem(index=1, a=23, b=4, operator="mul", c=92),
        tex_module.OpeProblem(index=2, a=48, b=6, operator="mul", c=288),
        tex_module.OpeProblem(index=3, a=90, b=9, operator="mul", c=810),
    ]
    blank, filled = tex_module.build_ope_page_pair(problems, 2, False, True)
    tex = tex_module.build_document_tex("A4", [blank], [filled], mode, engine_adapter)
    out_pdf_path = tmp_path / f"{engine_name}_{mode}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
