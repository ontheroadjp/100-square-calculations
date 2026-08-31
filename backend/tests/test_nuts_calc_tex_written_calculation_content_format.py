"""Tests for the shared "written calculation / hissan" content-format
components (taxonomy pattern 6) introduced by issue #269.

Issue #269 retrofits ``build_vertical_block_tex`` (``ope --vertical``) so its
multi-line written-calculation body is emitted through the shared
``\\verticalcalc`` / ``\\verticalcalcblank`` (xlop add/sub/mul) and
``\\longdivisioncalc`` / ``\\longdivisioncalcblank`` (longdivision div)
components, instead of a bare module-level ``\\opset`` option string with a
magic ``columnwidth=2ex`` literal.

- The column grid itself is still drawn by ``xlop`` / ``longdivision``; the
  shared macros only centralize the tuning points (``\\verticalcolumnwidth``
  etc., guidelines items 3, 4, 6, 11, 12, 16) and fold the blank vs
  answer-key switch into one place.
- Every centralized length equals the value already in effect (xlop's
  defaults), so the compiled PDFs are byte-for-byte unchanged -- this is a
  "name the magic numbers" retrofit.
- ``build_vertical_calc_tex`` returns the number-free body;
  ``build_vertical_block_tex`` only prepends the legacy ``n)\\newline ``
  prefix.

``ope --vertical`` is not on the internal presentation API (it routes
straight to the CLI tabular grid), so the real-PDF spot checks compile
through the legacy ``build_document_tex`` builder. Each is skipped when its
engine binary is absent (mirroring
test_nuts_calc_tex_staged_arrow_chain_content_format.py).
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def _problem(
    index: int = 1,
    a: int = 23,
    b: int = 4,
    operator: str = "add",
    c: int = 27,
    a_decimal_places: int = 0,
    b_decimal_places: int = 0,
) -> "tex_module.OpeProblem":
    return tex_module.OpeProblem(
        index=index,
        a=a,
        b=b,
        operator=operator,
        c=c,
        a_decimal_places=a_decimal_places,
        b_decimal_places=b_decimal_places,
    )


# --- shared macro block -----------------------------------------------------

def test_content_format_macros_define_the_written_calculation_components() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newlength{\\verticalcolumnwidth}" in macros
    assert (
        f"\\setlength{{\\verticalcolumnwidth}}{{{tex_module.CONTENT_FORMAT_VERTICAL_COLUMN_WIDTH_TEX}}}"
        in macros
    )
    assert "\\newlength{\\verticalrulewidth}" in macros
    assert (
        f"\\setlength{{\\verticalrulewidth}}{{{tex_module.CONTENT_FORMAT_VERTICAL_RULE_WIDTH_TEX}}}"
        in macros
    )
    assert "\\newlength{\\verticalrowheight}" in macros
    assert (
        f"\\setlength{{\\verticalrowheight}}{{{tex_module.CONTENT_FORMAT_VERTICAL_ROW_HEIGHT_TEX}}}"
        in macros
    )
    assert "\\newlength{\\verticaldecimalsepoffset}" in macros
    assert (
        f"\\setlength{{\\verticaldecimalsepoffset}}{{{tex_module.CONTENT_FORMAT_VERTICAL_DECIMAL_SEP_OFFSET_TEX}}}"
        in macros
    )

    # the one centralized xlop option group
    assert (
        "\\newcommand{\\verticalcalcsetup}{\\opset{voperator=bottom,"
        "columnwidth=\\verticalcolumnwidth,lineheight=\\verticalrowheight,"
        "hrulewidth=\\verticalrulewidth,vrulewidth=\\verticalrulewidth,"
        "decimalsepoffset=\\verticaldecimalsepoffset}}"
    ) in macros
    # Since issue #301 the wrappers own the serif hissan font + size track, and
    # the blank mul drops (not phantom-reserves) its partial-product rows.
    assert (
        "\\newcommand{\\verticalcalc}[1]{\\problemfractionstyle{\\hissandigitfont"
        "\\begingroup\\verticalcalcsetup #1\\endgroup}}"
        in macros
    )
    assert (
        "\\newcommand{\\verticalcalcblank}[1]{\\problemfractionstyle{\\hissandigitfont"
        "\\begingroup\\verticalcalcsetup"
        "\\opset{resultstyle=\\phantom,carrystyle=\\phantom,displayintermediary=None}"
        "#1\\endgroup}}"
    ) in macros
    assert (
        "\\newcommand{\\longdivisioncalc}[2]{\\problemfractionstyle{\\hissandigitfont"
        "$\\intlongdivision{#1}{#2}$}}"
        in macros
    )
    assert (
        "\\newcommand{\\longdivisioncalcblank}[2]{\\problemfractionstyle{\\hissandigitfont"
        "$\\intlongdivision[stage=0]{#1}{#2}$}}"
        in macros
    )

    # \makebox[ is deliberately NOT used here: #229's layout tests assert its
    # absence as a proxy for "the problem-number box was skipped".
    assert "\\makebox[" not in macros


def test_centralized_lengths_equal_xlop_defaults_so_pdfs_are_unchanged() -> None:
    # This is a "name the magic numbers" retrofit -- the values must not drift.
    assert tex_module.CONTENT_FORMAT_VERTICAL_COLUMN_WIDTH_TEX == "2ex"
    assert tex_module.CONTENT_FORMAT_VERTICAL_RULE_WIDTH_TEX == "0.4pt"
    assert tex_module.CONTENT_FORMAT_VERTICAL_ROW_HEIGHT_TEX == "\\baselineskip"
    assert tex_module.CONTENT_FORMAT_VERTICAL_DECIMAL_SEP_OFFSET_TEX == "0pt"


def test_content_format_macros_leave_the_pattern_1_to_5_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}" in macros
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros
    assert "\\newcommand{\\compareeq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\arroweq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractionarroweq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\stagedchaineq}[1]{$#1\\vphantom{0}$}" in macros


def test_macros_are_spliced_into_the_legacy_document_builder() -> None:
    blank, filled = tex_module.build_ope_page_pair([_problem()], 1, True, False)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\verticalcalcsetup}" in document
    assert document.index("\\newcommand{\\verticalcalcsetup}") < document.index("\\begin{document}")


# --- number-free body helper: build_vertical_calc_tex --------------------

@pytest.mark.parametrize(
    ("operator", "xlop_cmd"),
    [("add", "opadd"), ("sub", "opsub"), ("mul", "opmul")],
)
def test_build_vertical_calc_tex_add_sub_mul_wrap_the_xlop_call(operator: str, xlop_cmd: str) -> None:
    problem = _problem(a=123, b=45, operator=operator, c=0)

    filled = tex_module.build_vertical_calc_tex(problem, show_answer=True)
    blank = tex_module.build_vertical_calc_tex(problem, show_answer=False)

    assert filled == f"\\verticalcalc{{\\{xlop_cmd}{{123}}{{45}}}}"
    assert blank == f"\\verticalcalcblank{{\\{xlop_cmd}{{123}}{{45}}}}"


def test_build_vertical_calc_tex_div_wraps_the_longdivision_call() -> None:
    problem = _problem(a=144, b=12, operator="div", c=12)

    filled = tex_module.build_vertical_calc_tex(problem, show_answer=True)
    blank = tex_module.build_vertical_calc_tex(problem, show_answer=False)

    assert filled == "\\longdivisioncalc{144}{12}"
    assert blank == "\\longdivisioncalcblank{144}{12}"


def test_build_vertical_block_tex_is_prefix_plus_number_free_body() -> None:
    for operator, c in [("add", 27), ("sub", 19), ("mul", 92), ("div", 5)]:
        problem = _problem(index=3, a=20, b=4, operator=operator, c=c)
        for show_answer in (True, False):
            body = tex_module.build_vertical_calc_tex(problem, show_answer)
            block = tex_module.build_vertical_block_tex(problem, show_answer)
            assert block == f"3)\\newline {body}"


# --- Layer-3 slot formatter for the internal presentation API (issue #227) --

def test_build_vertical_ope_slot_content_tex_is_the_number_free_body() -> None:
    """The pattern-6 slot formatter (issue #227) is the number-free
    build_vertical_calc_tex body, with no embedded `n)` prefix -- mirroring
    build_ope_slot_content_tex vs build_horizontal_block_tex."""
    for operator, c in [("add", 27), ("sub", 19), ("mul", 92), ("div", 5)]:
        problem = _problem(index=7, a=48, b=12, operator=operator, c=c)
        for show_answer in (True, False):
            slot = tex_module.build_vertical_ope_slot_content_tex(problem, show_answer)
            assert slot == tex_module.build_vertical_calc_tex(problem, show_answer)
            assert not slot.startswith("7)")
            assert "\\newline" not in slot


def test_content_area_slot_tex_tabular_mode_centres_a_natural_width_hissan_unit() -> None:
    """issue #301: for grid_layout='tabular' the number sits on its own line
    above the block inside a natural-width inner tabular, so the grid column's
    \\centering centres it (a full-width \\parbox would pin the narrow hissan
    block to the column's left edge)."""
    layout = tex_module.ContentAreaLayout(rows=2, columns=2)
    body = "\\verticalcalc{\\opadd{48}{12}}"

    slot = tex_module.build_content_area_slot_tex(3, body, layout, grid_layout="tabular")

    assert slot == (
        "\\begin{tabular}{@{}l@{}}"
        "\\problemnumberstyle{3)}"
        f"\\\\[{tex_module.CONTENT_FORMAT_HISSAN_SLOT_GAP_TEX}]"
        f"{body}"
        "\\end{tabular}"
    )
    # no full-width parbox / makebox gutter in tabular mode
    assert "\\parbox" not in slot
    assert "\\makebox[" not in slot


# --- blanking mechanism is preserved ------------------------------------

def test_blank_add_uses_the_phantom_style_hooks_filled_does_not() -> None:
    problem = _problem(a=23, b=4, operator="add", c=27)

    blank = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled = tex_module.build_vertical_block_tex(problem, show_answer=True)

    assert "\\verticalcalcblank{" in blank
    assert "\\verticalcalc{" in filled
    # the \phantom hooks live inside the \verticalcalcblank macro body, not in
    # the emitted block -- the emitted block just names the macro.
    assert "\\phantom" not in blank
    assert "\\phantom" not in filled


def test_blank_div_keeps_stage_zero_filled_does_not() -> None:
    problem = _problem(a=144, b=12, operator="div", c=12)

    blank = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled = tex_module.build_vertical_block_tex(problem, show_answer=True)

    assert "\\longdivisioncalcblank{144}{12}" in blank
    assert "\\longdivisioncalc{144}{12}" in filled


# --- decimal operands flow through format_decimal_value unchanged ------

def test_decimal_operands_are_formatted_the_same_way_as_the_horizontal_builder() -> None:
    problem = _problem(
        a=125, b=375, operator="add", c=500,
        a_decimal_places=1, b_decimal_places=2,
    )

    body = tex_module.build_vertical_calc_tex(problem, show_answer=True)

    assert body == "\\verticalcalc{\\opadd{12.5}{3.75}}"


def test_mix_operator_is_never_seen_by_the_builder() -> None:
    # generate_ope_problems resolves 'mix' to a concrete operator per problem;
    # the builder only ever sees add/sub/mul/div.
    problem = _problem(a=8, b=3, operator="sub", c=5)
    body = tex_module.build_vertical_calc_tex(problem, show_answer=True)
    assert body == "\\verticalcalc{\\opsub{8}{3}}"


# --- real-PDF spot checks (both engines, all operators, blank + filled) --

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("mode", ["blank", "filled"])
def test_vertical_page_compiles_to_pdf(engine_name: str, mode: str, tmp_path: Path) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    problems = [
        tex_module.OpeProblem(index=1, a=23, b=4, operator="add", c=27),
        tex_module.OpeProblem(index=2, a=91, b=48, operator="sub", c=43),
        tex_module.OpeProblem(index=3, a=123, b=45, operator="mul", c=5535),
        tex_module.OpeProblem(index=4, a=144, b=12, operator="div", c=12),
    ]
    blank, filled = tex_module.build_ope_page_pair(problems, 2, True, False)
    tex = tex_module.build_document_tex("A4", [blank], [filled], mode, engine_adapter)
    out_pdf_path = tmp_path / f"{engine_name}_{mode}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_vertical_decimal_page_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    problems = [
        tex_module.OpeProblem(
            index=1, a=125, b=375, operator="add", c=500,
            a_decimal_places=1, b_decimal_places=2,
        ),
        tex_module.OpeProblem(
            index=2, a=875, b=25, operator="mul", c=21875,
            a_decimal_places=1, b_decimal_places=0,
        ),
    ]
    blank, filled = tex_module.build_ope_page_pair(problems, 2, True, False)
    tex = tex_module.build_document_tex("A4", [blank], [filled], "filled", engine_adapter)
    out_pdf_path = tmp_path / f"{engine_name}_decimal.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("show_answer", [False, True])
def test_vertical_presentation_document_compiles_to_pdf(
    engine_name: str, show_answer: bool, tmp_path: Path
) -> None:
    """Issue #227: the `ope --vertical` migration builds its document through
    the internal presentation API (build_presentation_document_tex) with the
    pattern-6 slot formatter, the Layer-2 numbered content area and the tabular
    grid the multi-row xlop / longdivision output needs. Compile it end to end
    with both engines, blank and answer-key, all four operators."""
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    problems = [
        tex_module.OpeProblem(index=1, a=23, b=4, operator="add", c=27),
        tex_module.OpeProblem(index=2, a=91, b=48, operator="sub", c=43),
        tex_module.OpeProblem(index=3, a=123, b=45, operator="mul", c=5535),
        tex_module.OpeProblem(index=4, a=144, b=12, operator="div", c=12),
    ]
    page = tex_module.PresentationPage(
        problems=problems, indices=[p.index for p in problems]
    )
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_vertical_ope_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=2, columns=2),
        engine_adapter=engine_adapter,
        show_answer=show_answer,
        grid_layout="tabular",
    )
    assert "\\begin{tabular}" in tex
    # the Layer-2 numbered slot was composed: since issue #301 the tabular-mode
    # slot uses a natural-width inner tabular with the number on its own line
    # (not a \makebox gutter -- that shape is inline-only).
    assert "\\begin{tabular}{@{}l@{}}\\problemnumberstyle{" in tex
    out_pdf_path = tmp_path / f"{engine_name}_{show_answer}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
