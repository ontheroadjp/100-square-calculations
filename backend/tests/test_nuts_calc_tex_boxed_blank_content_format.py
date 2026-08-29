"""Tests for the shared "boxed-blank equation" content-format component
(taxonomy pattern 2) introduced by issue #265.

Issue #265 retrofits the two pattern-2 builders -- ``build_com_*`` (``com``,
fixed ``a + [box] = target``) and ``build_missing_value_*``
(``ope --missing-value``, either operand boxed, any of add/sub/mul/div) --
so their number-free Layer-3 body is emitted through the shared
``\\boxedblankeq`` wrapper, the centralized ``\\opspace`` operator gap
(reused from issue #264), and the shared ``\\boxedblank`` operand marker,
instead of a raw ``$...$`` f-string that inlined ``BOXED_BLANK_TEX``.

``BOXED_BLANK_TEX`` itself is untouched (pattern 3's
``build_fraction_comparison_*`` still uses it verbatim); pattern 2 now
references the new ``BOXED_BLANK_OPERAND_TEX`` (== ``\\boxedblank``) instead.

Most tests here are pure-Python (assert the generated TeX string). A few
compile a real PDF via the presentation API (``com`` filled,
``ope --missing-value`` a-blank / b-blank / filled) and run under both
pdflatex and lualatex; each is skipped when its engine binary is absent
(mirroring test_nuts_calc_tex_equation_content_format.py).
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


# --- shared macro block -----------------------------------------------------

def test_content_format_macros_define_the_boxed_blank_components() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newlength{\\boxedblankwidth}" in macros
    assert (
        f"\\setlength{{\\boxedblankwidth}}{{{tex_module.CONTENT_FORMAT_BOXED_BLANK_WIDTH_TEX}}}"
        in macros
    )
    # Baseline-anchored: an \fbox + invisible strut, NOT \vcenter.
    assert (
        "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}"
        in macros
    )
    assert "\\vcenter" not in macros
    # $...$ wrapper + \vphantom so the filled (no-box) row keeps the blank row's height.
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros


def test_content_format_macros_leave_the_pattern_1_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}" in macros


def test_boxed_blank_operand_marker_is_the_macro_call_not_the_raw_box() -> None:
    assert tex_module.BOXED_BLANK_OPERAND_TEX == "\\boxedblank"
    # pattern 3's raw constant is unchanged
    assert tex_module.BOXED_BLANK_TEX == "\\vcenter{\\hbox{\\fbox{\\rule{0pt}{1em}\\hspace{1em}}}}"


def test_macros_are_spliced_into_the_legacy_document_builder() -> None:
    problems = [tex_module.ComProblem(index=1, a=3, target=7, c=4)]
    blank, filled = tex_module.build_com_page_pair(problems, 1)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\boxedblankeq}" in document
    assert document.index("\\newcommand{\\boxedblank}") < document.index("\\begin{document}")


def test_macros_are_spliced_into_the_presentation_document_builder() -> None:
    problems = [tex_module.ComProblem(index=1, a=3, target=7, c=4)]
    page = tex_module.PresentationPage(problems=problems, indices=[1])
    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "\\newcommand{\\boxedblankeq}" in document
    assert document.index("\\newcommand{\\boxedblank}") < document.index("\\begin{document}")


# --- equation body helper -------------------------------------------------

def test_build_boxed_blank_equation_tex_wraps_via_boxedblankeq() -> None:
    body = tex_module.build_boxed_blank_equation_tex(
        "8 \\opspace + \\opspace \\boxedblank", "10"
    )
    assert body == "\\boxedblankeq{8 \\opspace + \\opspace \\boxedblank \\opspace = \\opspace 10}"


# --- com: fixed a + [box] = target --------------------------------------

def test_com_slot_content_blank_boxes_the_result_operand() -> None:
    problem = tex_module.ComProblem(index=5, a=37, target=100, c=63)

    blank = tex_module.build_com_slot_content_tex(problem, show_answer=False)
    filled = tex_module.build_com_slot_content_tex(problem, show_answer=True)

    assert blank == (
        "\\boxedblankeq{37 \\opspace + \\opspace \\boxedblank \\opspace = \\opspace 100}"
    )
    assert filled == "\\boxedblankeq{37 \\opspace + \\opspace 63 \\opspace = \\opspace 100}"
    assert "5)" not in blank
    assert "63" not in blank


def test_com_block_tex_is_number_prefix_plus_slot_body() -> None:
    problem = tex_module.ComProblem(index=5, a=37, target=100, c=63)

    for show_answer in (False, True):
        block = tex_module.build_com_block_tex(problem, show_answer)
        slot = tex_module.build_com_slot_content_tex(problem, show_answer)
        assert block == f"5) {slot}"


# --- ope --missing-value: either operand boxed, any operator ------------

_MV_SYMBOLS = {"add": "+", "sub": "-", "mul": "\\times", "div": "\\div"}


@pytest.mark.parametrize("operator", sorted(_MV_SYMBOLS))
def test_missing_value_slot_content_boxes_b_for_every_operator(operator: str) -> None:
    problem = tex_module.MissingValueProblem(
        index=3, a=8, b=2, operator=operator, c=10, blank="b",
    )
    symbol = _MV_SYMBOLS[operator]

    blank = tex_module.build_missing_value_slot_content_tex(problem, show_answer=False)
    filled = tex_module.build_missing_value_slot_content_tex(problem, show_answer=True)

    assert blank == (
        f"\\boxedblankeq{{8 \\opspace {symbol} \\opspace \\boxedblank \\opspace = \\opspace 10}}"
    )
    assert filled == (
        f"\\boxedblankeq{{8 \\opspace {symbol} \\opspace 2 \\opspace = \\opspace 10}}"
    )


def test_missing_value_slot_content_boxes_a_when_blank_is_a() -> None:
    problem = tex_module.MissingValueProblem(
        index=1, a=2, b=3, operator="add", c=5, blank="a",
    )

    blank = tex_module.build_missing_value_slot_content_tex(problem, show_answer=False)

    assert blank == (
        "\\boxedblankeq{\\boxedblank \\opspace + \\opspace 3 \\opspace = \\opspace 5}"
    )


def test_missing_value_always_shows_the_result_even_in_the_blank_variant() -> None:
    for blank in tex_module.MISSING_VALUE_POSITIONS:
        problem = tex_module.MissingValueProblem(
            index=1, a=2, b=3, operator="add", c=5, blank=blank,
        )
        blank_tex = tex_module.build_missing_value_slot_content_tex(problem, show_answer=False)
        # the result side never carries the box
        assert blank_tex.endswith("\\opspace = \\opspace 5}")
        assert tex_module.BOXED_BLANK_OPERAND_TEX not in blank_tex.split("= \\opspace")[-1]


@pytest.mark.parametrize("blank", ["a", "b"])
def test_missing_value_block_tex_is_number_prefix_plus_slot_body(blank: str) -> None:
    problem = tex_module.MissingValueProblem(
        index=9, a=8, b=2, operator="sub", c=6, blank=blank,
    )
    for show_answer in (False, True):
        block = tex_module.build_missing_value_block_tex(problem, show_answer)
        slot = tex_module.build_missing_value_slot_content_tex(problem, show_answer)
        assert block == f"9) {slot}"


# --- real-PDF spot checks (both engines) --------------------------------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


def _compile_single_slot_pdf(engine_name, content_format, problems, indices, tmp_path, show_answer):
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    page = tex_module.PresentationPage(problems=problems, indices=indices)
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=content_format,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=engine_adapter,
        show_answer=show_answer,
    )
    out_pdf_path = tmp_path / f"{engine_name}_slot.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_com_slot_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_com_slot_content_tex,
        [tex_module.ComProblem(index=1, a=37, target=100, c=63)],
        [1],
        tmp_path,
        show_answer=True,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("blank", ["a", "b"])
def test_missing_value_blank_slot_compiles_to_pdf(engine_name: str, blank: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_missing_value_slot_content_tex,
        [tex_module.MissingValueProblem(index=1, a=128, b=64, operator="mul", c=8192, blank=blank)],
        [1],
        tmp_path,
        show_answer=False,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_missing_value_filled_slot_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_missing_value_slot_content_tex,
        [tex_module.MissingValueProblem(index=1, a=128, b=64, operator="mul", c=8192, blank="b")],
        [1],
        tmp_path,
        show_answer=True,
    )
