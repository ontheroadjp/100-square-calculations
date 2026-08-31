"""Tests for the shared "comparison" content-format component (taxonomy
pattern 3) introduced by issue #266.

Issue #266 retrofits ``build_fraction_comparison_*`` (``compare``) so its
number-free Layer-3 body is emitted through the shared ``\\compareeq``
wrapper and the centralized ``\\opspace`` gap (reused from issue #264)
around the relation symbol, instead of a raw ``$\\displaystyle ...$``
f-string that inlined ``BOXED_BLANK_TEX``.

- The blanked relation symbol reuses pattern 2's shared ``\\boxedblank``
  marker (``COMPARE_REL_BLANK_TEX``), so the blanked slot looks identical
  across the two formats and shares ``\\boxedblankwidth``.
- Int/decimal operands are ``\\vcenter``-wrapped so they sit on the math
  axis alongside a ``\\frac`` operand (guidelines item 17); a ``\\frac``
  (plain or mixed-number) is already axis-centered and left bare.
- The old raw ``\\vcenter`` ``BOXED_BLANK_TEX`` constant is removed --
  pattern 3 was its last user.

Most tests here are pure-Python (assert the generated TeX string). A few
compile a real PDF via the presentation API across int/decimal/fraction
operand kinds and run under both pdflatex and lualatex; each is skipped
when its engine binary is absent (mirroring
test_nuts_calc_tex_boxed_blank_content_format.py).
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def _int(value: int) -> "tex_module.FractionComparisonOperand":
    return tex_module.FractionComparisonOperand(value, 1, 0, "int")


def _decimal(scaled: int, places: int = 1) -> "tex_module.FractionComparisonOperand":
    return tex_module.FractionComparisonOperand(scaled, 10 ** places, 0, "decimal", places)


def _frac(numerator: int, denominator: int, whole: int = 0) -> "tex_module.FractionComparisonOperand":
    return tex_module.FractionComparisonOperand(numerator, denominator, whole, "fraction")


# --- shared macro block -----------------------------------------------------

def test_content_format_macros_define_the_comparison_wrapper() -> None:
    macros = tex_module.build_content_format_macros_tex()

    # $\displaystyle ...$ + a display-fraction height strut for a uniform row
    # height across int/decimal/\frac operand mixes.
    assert (
        "\\newcommand{\\compareeq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}"
        in macros
    )


def test_content_format_macros_leave_the_pattern_1_and_2_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}" in macros
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros


def test_comparison_reuses_pattern_2_boxed_blank_marker() -> None:
    assert tex_module.COMPARE_REL_BLANK_TEX == "\\boxedblank"
    assert tex_module.COMPARE_REL_BLANK_TEX == tex_module.BOXED_BLANK_OPERAND_TEX
    # the old raw \vcenter box constant is gone (pattern 3 was its last user)
    assert not hasattr(tex_module, "BOXED_BLANK_TEX")


def test_macros_are_spliced_into_the_legacy_document_builder() -> None:
    problems = [tex_module.FractionComparisonProblem(1, _frac(1, 2), _frac(2, 3))]
    blank, filled = tex_module.build_fraction_comparison_page_pair(problems, 1)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\compareeq}" in document
    assert document.index("\\newcommand{\\compareeq}") < document.index("\\begin{document}")


def test_macros_are_spliced_into_the_presentation_document_builder() -> None:
    problems = [tex_module.FractionComparisonProblem(1, _frac(1, 2), _frac(2, 3))]
    page = tex_module.PresentationPage(problems=problems, indices=[1])
    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_fraction_comparison_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "\\newcommand{\\compareeq}" in document
    assert document.index("\\newcommand{\\compareeq}") < document.index("\\begin{document}")


# --- relational body helper ----------------------------------------------

def test_build_comparison_equation_tex_wraps_via_compareeq_with_opspace() -> None:
    body = tex_module.build_comparison_equation_tex("\\frac{1}{2}", "<", "\\frac{2}{3}")
    assert body == "\\compareeq{\\frac{1}{2} \\opspace < \\opspace \\frac{2}{3}}"


# --- operand rendering: vertical centering (item 17) --------------------

def test_comparison_operand_int_and_decimal_are_vcenter_wrapped() -> None:
    assert tex_module.comparison_operand_to_tex(_int(7)) == "\\vcenter{\\hbox{$7$}}"
    assert tex_module.comparison_operand_to_tex(_decimal(5, 1)) == "\\vcenter{\\hbox{$0.5$}}"


def test_comparison_operand_fraction_and_mixed_number_stay_bare() -> None:
    # a \frac already straddles the math axis in \displaystyle, so it is not wrapped.
    assert tex_module.comparison_operand_to_tex(_frac(1, 2)) == "\\frac{1}{2}"
    assert tex_module.comparison_operand_to_tex(_frac(1, 3, 2)) == "2\\frac{1}{3}"


# --- slot bodies: blank vs filled, every operand-kind mix --------------

def test_fraction_comparison_slot_fraction_vs_fraction() -> None:
    problem = tex_module.FractionComparisonProblem(5, _frac(1, 2), _frac(2, 3))

    blank = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=False)
    filled = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)

    assert blank == "\\compareeq{\\frac{1}{2} \\opspace \\boxedblank \\opspace \\frac{2}{3}}"
    assert filled == "\\compareeq{\\frac{1}{2} \\opspace < \\opspace \\frac{2}{3}}"
    assert "5)" not in blank


def test_fraction_comparison_slot_int_vs_fraction() -> None:
    problem = tex_module.FractionComparisonProblem(1, _int(3), _frac(2, 3))

    blank = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=False)
    filled = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)

    assert blank == (
        "\\compareeq{\\vcenter{\\hbox{$3$}} \\opspace \\boxedblank \\opspace \\frac{2}{3}}"
    )
    assert filled == (
        "\\compareeq{\\vcenter{\\hbox{$3$}} \\opspace > \\opspace \\frac{2}{3}}"
    )


def test_fraction_comparison_slot_decimal_vs_fraction() -> None:
    problem = tex_module.FractionComparisonProblem(1, _decimal(5, 1), _frac(3, 4))

    filled = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)

    assert filled == (
        "\\compareeq{\\vcenter{\\hbox{$0.5$}} \\opspace < \\opspace \\frac{3}{4}}"
    )


def test_fraction_comparison_slot_int_vs_int() -> None:
    problem = tex_module.FractionComparisonProblem(1, _int(5), _int(2))

    filled = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)

    assert filled == (
        "\\compareeq{\\vcenter{\\hbox{$5$}} \\opspace > \\opspace \\vcenter{\\hbox{$2$}}}"
    )


def test_fraction_comparison_slot_mixed_number_operand() -> None:
    problem = tex_module.FractionComparisonProblem(1, _frac(1, 3, 2), _frac(1, 2))

    filled = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)

    assert filled == (
        "\\compareeq{2\\frac{1}{3} \\opspace > \\opspace \\frac{1}{2}}"
    )


def test_fraction_comparison_block_tex_is_number_prefix_plus_slot_body() -> None:
    problem = tex_module.FractionComparisonProblem(9, _int(3), _frac(2, 3))

    for show_answer in (False, True):
        block = tex_module.build_fraction_comparison_block_tex(problem, show_answer)
        slot = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer)
        assert block == f"9) {slot}"


def test_fraction_comparison_block_slot_equivalence_via_content_area_slot() -> None:
    problem = tex_module.FractionComparisonProblem(5, _frac(1, 2), _frac(2, 3))
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)
    composed = tex_module.build_content_area_slot_tex(problem.index, slot, layout)

    # Since the issue #301 type scale the composed slot wraps the number and
    # content in the \problemnumberstyle / \problemcontentstyle macros, so it
    # deliberately diverges from the legacy "N) " + body prefix (asserted next).
    assert composed == (
        f"\\makebox[0mm][r]{{\\problemnumberstyle{{{problem.index})}}}}"
        f"\\hspace{{{tex_module.CONTENT_AREA_NUMBER_GAP_MM}mm}}"
        f"\\parbox[t]{{\\dimexpr\\linewidth-0mm-{tex_module.CONTENT_AREA_NUMBER_GAP_MM}mm\\relax}}"
        f"{{\\raggedright\\problemcontentstyle{{{slot}}}\\par}}"
    )
    assert tex_module.build_fraction_comparison_block_tex(problem, True) == f"{problem.index}) {slot}"


# --- real-PDF spot checks (both engines, every operand-kind mix) -------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}

_OPERAND_PAIRS = {
    "frac_frac": (_frac(1, 2), _frac(2, 3)),
    "int_frac": (_int(3), _frac(2, 3)),
    "decimal_frac": (_decimal(5, 1), _frac(3, 4)),
    "int_int": (_int(5), _int(2)),
    "mixed_frac": (_frac(1, 3, 2), _frac(1, 2)),
}


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("pair_name", sorted(_OPERAND_PAIRS))
@pytest.mark.parametrize("show_answer", [False, True])
def test_compare_slot_compiles_to_pdf(
    engine_name: str, pair_name: str, show_answer: bool, tmp_path: Path
) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    a, b = _OPERAND_PAIRS[pair_name]
    engine_adapter = _ENGINES[engine_name]()
    page = tex_module.PresentationPage(
        problems=[tex_module.FractionComparisonProblem(1, a, b)], indices=[1]
    )
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_fraction_comparison_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=engine_adapter,
        show_answer=show_answer,
    )
    out_pdf_path = tmp_path / f"{engine_name}_{pair_name}_{show_answer}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
