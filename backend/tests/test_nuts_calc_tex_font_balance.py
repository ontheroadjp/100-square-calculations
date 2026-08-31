"""Tests for the worksheet type scale (issue #301).

The drill sheets had no typographic hierarchy: the problem number, the
equation, the field labels and the footer were all ~12pt, and the equation
-- the primary content -- read smaller and lighter than the problem number
next to it. Issue #301 introduces a type scale: the equation leads (enlarged,
on two size tracks so a display fraction doesn't crowd its row), the problem
number is a small grey index, and the running chrome recedes. The equation
font is left as the engine default (Computer Modern).

Pure-Python tests assert the generated TeX. A handful compile a real PDF via
the presentation API under both engines (skipped when the engine binary is
absent, mirroring test_nuts_calc_tex_equation_content_format.py); the
vertical-calc ones guard that the enlarged xlop/longdivision block still
lays its columns out cleanly.
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


# --- type-scale macros -----------------------------------------------------

def test_content_format_macros_define_the_problem_number_and_content_styles() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert (
        f"\\newcommand{{\\problemnumberstyle}}[1]{{{{{tex_module.PROBLEM_NUMBER_FONT_SIZE_TEX}"
        f"\\color{{{tex_module.PROBLEM_NUMBER_TEXT_COLOR_TEX}}}#1}}}}"
        in macros
    )
    assert (
        f"\\newcommand{{\\problemcontentstyle}}[1]"
        f"{{{{{tex_module.PROBLEM_CONTENT_FONT_SIZE_DENSE_TEX} #1}}}}"
        in macros
    )
    assert (
        f"\\newcommand{{\\problemfractionstyle}}[1]"
        f"{{{{{tex_module.PROBLEM_FRACTION_FONT_SIZE_DENSE_TEX} #1}}}}"
        in macros
    )


def test_slot_composition_routes_number_and_content_through_the_type_scale() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=8)

    slot = tex_module.build_content_area_slot_tex(7, "\\horizontaleq{1 + 2 = 3}", layout)

    gap = tex_module.CONTENT_AREA_NUMBER_GAP_MM
    assert slot == (
        "\\makebox[8mm][r]{\\problemnumberstyle{7)}}"
        f"\\hspace{{{gap}mm}}"
        f"\\parbox[t]{{\\dimexpr\\linewidth-8mm-{gap}mm\\relax}}"
        "{\\raggedright\\problemcontentstyle{\\horizontaleq{1 + 2 = 3}}\\par}"
    )


def test_slot_pieces_span_the_full_column_so_centering_cannot_shift_them() -> None:
    # number box + gap + (\linewidth - box - gap) parbox == \linewidth, so the
    # grid's \centering has no slack: the number gutter and the equation start
    # each stay at a constant x, even when content width varies wildly
    # (grade-3 parenthesised expressions at the enlarged size).
    gap = tex_module.CONTENT_AREA_NUMBER_GAP_MM
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=12)

    slot = tex_module.build_content_area_slot_tex(1, "\\horizontaleq{X}", layout)

    assert slot.startswith(f"\\makebox[12mm][r]{{\\problemnumberstyle{{1)}}}}\\hspace{{{gap}mm}}")
    assert f"\\parbox[t]{{\\dimexpr\\linewidth-12mm-{gap}mm\\relax}}{{\\raggedright" in slot


def test_fraction_family_wrappers_step_down_to_the_fraction_track() -> None:
    # A display \frac at the plain content size crowds its row, so the three
    # fraction-bearing wrappers set \problemfractionstyle inside, which (being
    # an absolute size command) overrides the slot's \problemcontentstyle.
    macros = tex_module.build_content_format_macros_tex()

    for wrapper in ("\\fractioneq", "\\compareeq", "\\fractionarroweq"):
        assert f"\\newcommand{{{wrapper}}}[1]{{\\problemfractionstyle{{$\\displaystyle #1" in macros
    # the single-line wrappers stay bare (plain track via the slot).
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\arroweq}[1]{$#1$}" in macros


def test_number_box_and_gap_keep_a_tight_constant_gutter() -> None:
    # The number is right-aligned in the box (so every "N)" ends at the same x
    # whether 1- or 3-digit), then a small fixed gap to the left-aligned
    # equation -- number and equation read as two separate fields.
    assert tex_module.CONTENT_AREA_NUMBER_BOX_WIDTH_MM == 8
    assert tex_module.CONTENT_AREA_NUMBER_GAP_MM == 3


# --- density-aware content size ------------------------------------------

def test_content_style_override_promotes_sparse_pages_on_both_tracks() -> None:
    layout = tex_module.ContentAreaLayout(rows=5, columns=2)  # 10 slots

    override = tex_module.build_problem_content_style_override_tex(layout)

    assert override == (
        f"\\renewcommand{{\\problemcontentstyle}}[1]"
        f"{{{{{tex_module.PROBLEM_CONTENT_FONT_SIZE_SPARSE_TEX} #1}}}}\n"
        f"\\renewcommand{{\\problemfractionstyle}}[1]"
        f"{{{{{tex_module.PROBLEM_FRACTION_FONT_SIZE_SPARSE_TEX} #1}}}}\n"
    )


def test_content_style_override_leaves_dense_pages_on_the_default_step() -> None:
    layout = tex_module.ContentAreaLayout(rows=10, columns=3)  # 30 slots

    assert tex_module.build_problem_content_style_override_tex(layout) == ""


def test_content_style_override_boundary_is_inclusive() -> None:
    at_limit = tex_module.ContentAreaLayout(
        rows=tex_module.CONTENT_DENSITY_SPARSE_MAX_SLOTS, columns=1
    )
    over_limit = tex_module.ContentAreaLayout(
        rows=tex_module.CONTENT_DENSITY_SPARSE_MAX_SLOTS + 1, columns=1
    )

    assert tex_module.build_problem_content_style_override_tex(at_limit) != ""
    assert tex_module.build_problem_content_style_override_tex(over_limit) == ""


def test_content_style_override_skips_unnumbered_and_rowless_layouts() -> None:
    unnumbered = tex_module.ContentAreaLayout(rows=2, columns=2, numbered=False)
    rowless = tex_module.ContentAreaLayout(rows=None, columns=2)

    assert tex_module.build_problem_content_style_override_tex(unnumbered) == ""
    assert tex_module.build_problem_content_style_override_tex(rowless) == ""


def test_presentation_document_emits_the_sparse_override_after_the_macros() -> None:
    problems = [tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5)]
    page = tex_module.PresentationPage(problems=problems, indices=[1])

    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_ope_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=5, columns=2),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "\\renewcommand{\\problemcontentstyle}" in document
    assert document.index("\\newcommand{\\problemcontentstyle}") < document.index(
        "\\renewcommand{\\problemcontentstyle}"
    )
    assert document.index("\\renewcommand{\\problemcontentstyle}") < document.index(
        "\\begin{document}"
    )


def test_presentation_document_omits_the_override_on_dense_pages() -> None:
    problems = [
        tex_module.OpeProblem(index=i, a=2, b=3, operator="add", c=5) for i in range(1, 31)
    ]
    page = tex_module.PresentationPage(problems=problems, indices=list(range(1, 31)))

    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_ope_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=10, columns=3),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "\\renewcommand{\\problemcontentstyle}" not in document


# --- receding chrome -----------------------------------------------------

def test_running_chrome_recedes_to_small_grey() -> None:
    preamble = tex_module.build_page_shell_preamble_tex(
        tex_module.DEFAULT_PAGE_SHELL, "A4", tex_module.PdflatexEngineAdapter()
    )
    header = tex_module.build_page_shell_header_tex(tex_module.DEFAULT_PAGE_SHELL)

    assert (
        f"\\fancyfoot[L]{{\\footnotesize\\color{{{tex_module.CHROME_TEXT_COLOR_TEX}}}"
        in preamble
    )
    assert (
        f"\\fancyfoot[R]{{\\footnotesize\\color{{{tex_module.CHROME_TEXT_COLOR_TEX}}}Page"
        in preamble
    )
    assert (
        f"{{\\small\\color{{{tex_module.SUBTITLE_TEXT_COLOR_TEX}}} "
        f"{tex_module.SUB_TITLE_STR}}}" in header
    )


def test_field_labels_stay_plain_black_normalsize() -> None:
    # The Date/Time/Name write-in fields are deliberately left unstyled: they
    # already recede next to the enlarged problems and greying the labels is
    # not worth the fuss (see build_page_shell_header_tex).
    header = tex_module.build_page_shell_header_tex(
        tex_module.DEFAULT_PAGE_SHELL, with_name_field=True
    )

    assert "Date: \\underline{\\hspace{4cm}}" in header
    assert "Name: \\underline{\\hspace{8cm}}" in header


# --- real-PDF spot checks (both engines) --------------------------------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


def _compile_presentation_pdf(engine_name, content_format, problems, layout, tmp_path, *, grid_layout="inline"):
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    page = tex_module.PresentationPage(problems=problems, indices=[p.index for p in problems])
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=content_format,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=engine_adapter,
        show_answer=True,
        grid_layout=grid_layout,
    )
    out_pdf_path = tmp_path / f"{engine_name}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_horizontal_equation_compiles_under_the_type_scale(engine_name, tmp_path) -> None:
    _compile_presentation_pdf(
        engine_name,
        tex_module.build_ope_slot_content_tex,
        [tex_module.OpeProblem(index=1, a=2, b=7, operator="add", c=9)],
        tex_module.ContentAreaLayout(rows=5, columns=2),  # sparse -> \Large
        tmp_path,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_fraction_equation_compiles_under_the_type_scale(engine_name, tmp_path) -> None:
    _compile_presentation_pdf(
        engine_name,
        tex_module.build_fraction_slot_content_tex,
        [
            tex_module.FractionProblem(
                index=1, a=tex_module.Fraction(1, 2), b=tex_module.Fraction(3, 4),
                operator="add", c=tex_module.Fraction(5, 4),
            )
        ],
        tex_module.ContentAreaLayout(rows=5, columns=2),
        tmp_path,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_vertical_calc_columns_survive_the_enlarged_content_style(engine_name, operator, tmp_path) -> None:
    # The #301 regression guard: \problemcontentstyle enlarges the whole
    # xlop/longdivision block. Column alignment comes from xlop's \columnwidth,
    # so the enlarged vertical layout has to keep compiling cleanly.
    a, b = (48, 6) if operator == "div" else (57, 8)
    problem = tex_module.OpeProblem(
        index=1, a=a, b=b, operator=operator, c=(a // b if operator == "div" else 0),
    )
    _compile_presentation_pdf(
        engine_name,
        tex_module.build_vertical_ope_slot_content_tex,
        [problem],
        tex_module.ContentAreaLayout(rows=2, columns=2),
        tmp_path,
        grid_layout="tabular",
    )
