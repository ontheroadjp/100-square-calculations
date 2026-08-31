"""Tests for the shared "arrow-conversion" content-format components
(taxonomy patterns 4a / 4b / 4c) introduced by issue #267.

Issue #267 retrofits every pattern-4 builder so its number-free Layer-3
body is emitted through shared, guidelines-doc-compliant components
instead of raw ``$...$`` / ``$\\displaystyle ...$`` f-strings:

- 4a (``aBc``, ``evenodd``, ``multiples``, ``divisors``): the plain
  ``\\arroweq`` wrapper -- ``A => B`` where ``\\Rightarrow`` gets the
  centralized ``\\opspace`` gap on both sides (reused from issue #264).
- 4b (``simplify``, ``frac2dec``, ``dec2frac``): the ``\\fractionarroweq``
  wrapper -- same ``$\\displaystyle ...\\vphantom{\\frac{0}{0}}$`` shape as
  ``\\fractioneq``/``\\compareeq`` so blank and answer-key rows stay the
  same height across ``\\frac`` / integer / decimal / blank sides.
- 4c (``commondenom``): the two-element-pair helper
  ``build_fraction_pair_conversion_tex`` joins ``A, B`` and delegates to the
  same ``\\fractionarroweq`` wrapper.

The 4 duplicating ``build_*_block_tex`` (``aBc``, ``evenodd``,
``multiples``, ``divisors``) collapse to ``"n) " + slot`` (the other 4
already delegated). The RHS blank stays the shared unboxed
``BLANK_ANSWER_TEX`` marker (contrast with patterns 2/3's ``\\boxedblank``).

Most tests here are pure-Python (assert the generated TeX string). A few
compile a real PDF via the presentation API across 4a/4b/4c and run under
both pdflatex and lualatex; each is skipped when its engine binary is
absent (mirroring test_nuts_calc_tex_comparison_content_format.py).
"""

import shutil
import sys
from fractions import Fraction
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

BLANK = tex_module.BLANK_ANSWER_TEX


# --- problem factories ----------------------------------------------------

def _abc() -> "tex_module.AbcProblem":
    return tex_module.AbcProblem(index=5, a=1, b=2, c=3, d=4)


def _evenodd() -> "tex_module.EvenOddProblem":
    return tex_module.EvenOddProblem(index=5, a=6, is_even=True)


def _multiples() -> "tex_module.MultiplesProblem":
    return tex_module.MultiplesProblem(index=5, a=6, multiples=[6, 12, 18, 24])


def _divisors() -> "tex_module.DivisorsProblem":
    return tex_module.DivisorsProblem(index=5, a=12, divisors=[1, 2, 3, 4, 6, 12])


def _simplify() -> "tex_module.SimplifyProblem":
    return tex_module.SimplifyProblem(
        index=5, operand=tex_module.FractionOperand(18, 24), reduced=Fraction(3, 4)
    )


def _frac2dec() -> "tex_module.Frac2DecProblem":
    return tex_module.Frac2DecProblem(
        index=5, operand=tex_module.FractionOperand(3, 4), decimal_places=2, scaled_numerator=75
    )


def _dec2frac() -> "tex_module.Dec2FracProblem":
    return tex_module.Dec2FracProblem(
        index=5, decimal_places=1, scaled_numerator=6, reduced=Fraction(3, 5)
    )


def _commondenom() -> "tex_module.CommonDenomProblem":
    return tex_module.CommonDenomProblem(
        index=5,
        a=tex_module.FractionOperand(1, 3),
        b=tex_module.FractionOperand(1, 4),
        a_converted=tex_module.FractionOperand(4, 12),
        b_converted=tex_module.FractionOperand(3, 12),
    )


# --- shared macro block -------------------------------------------------

def test_content_format_macros_define_the_arrow_conversion_wrappers() -> None:
    macros = tex_module.build_content_format_macros_tex()

    # 4a: plain $...$ wrapper (same shape as \horizontaleq).
    assert "\\newcommand{\\arroweq}[1]{$#1$}" in macros
    # 4b/4c: $\displaystyle ...$ + display-fraction height strut for a
    # uniform row height across \frac/int/decimal/blank sides.
    assert (
        "\\newcommand{\\fractionarroweq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}"
        in macros
    )


def test_content_format_macros_leave_the_pattern_1_2_3_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}" in macros
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros
    assert "\\newcommand{\\compareeq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros


def test_arrow_conversion_rhs_blank_is_the_shared_unboxed_marker() -> None:
    # pattern 4 keeps the tail-blank unboxed (contrast patterns 2/3).
    assert BLANK == "\\hspace{1.5em}"
    blank_body = tex_module.build_abc_slot_content_tex(_abc(), show_answer=False)
    assert blank_body.endswith(f"\\opspace {BLANK}}}")
    assert "\\boxedblank" not in blank_body


@pytest.mark.parametrize(
    "page_pair_builder, slot_format",
    [
        (tex_module.build_abc_page_pair, tex_module.build_abc_slot_content_tex),
        (tex_module.build_simplify_page_pair, tex_module.build_simplify_slot_content_tex),
        (tex_module.build_commondenom_page_pair, tex_module.build_commondenom_slot_content_tex),
    ],
)
def test_macros_are_spliced_into_the_legacy_document_builder(page_pair_builder, slot_format) -> None:
    problems = {
        tex_module.build_abc_page_pair: [_abc()],
        tex_module.build_simplify_page_pair: [_simplify()],
        tex_module.build_commondenom_page_pair: [_commondenom()],
    }[page_pair_builder]
    blank, filled = page_pair_builder(problems, 1)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\arroweq}" in document
    assert "\\newcommand{\\fractionarroweq}" in document
    assert document.index("\\newcommand{\\arroweq}") < document.index("\\begin{document}")


def test_macros_are_spliced_into_the_presentation_document_builder() -> None:
    page = tex_module.PresentationPage(problems=[_simplify()], indices=[1])
    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_simplify_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "\\newcommand{\\arroweq}" in document
    assert "\\newcommand{\\fractionarroweq}" in document
    assert document.index("\\newcommand{\\fractionarroweq}") < document.index("\\begin{document}")


# --- conversion body helpers -----------------------------------------------

def test_build_arrow_conversion_tex_wraps_via_arroweq_with_opspace() -> None:
    assert tex_module.build_arrow_conversion_tex("1234", "154") == (
        "\\arroweq{1234 \\opspace \\Rightarrow \\opspace 154}"
    )


def test_build_fraction_arrow_conversion_tex_wraps_via_fractionarroweq() -> None:
    assert tex_module.build_fraction_arrow_conversion_tex("\\frac{3}{4}", "0.75") == (
        "\\fractionarroweq{\\frac{3}{4} \\opspace \\Rightarrow \\opspace 0.75}"
    )


def test_build_fraction_pair_conversion_tex_joins_the_left_pair_and_reuses_4b_wrapper() -> None:
    assert tex_module.build_fraction_pair_conversion_tex("\\frac{1}{3}", "\\frac{1}{4}", "X") == (
        "\\fractionarroweq{\\frac{1}{3}, \\frac{1}{4} \\opspace \\Rightarrow \\opspace X}"
    )


# --- exact slot bodies: blank vs filled, every pattern-4 command ---------

@pytest.mark.parametrize(
    "slot_format, problem, filled_body, blank_lhs",
    [
        (
            tex_module.build_abc_slot_content_tex, _abc(),
            "\\arroweq{1234 \\opspace \\Rightarrow \\opspace 154}", "1234",
        ),
        (
            tex_module.build_evenodd_slot_content_tex, _evenodd(),
            "\\arroweq{6 \\opspace \\Rightarrow \\opspace \\mathrm{even}}", "6",
        ),
        (
            tex_module.build_multiples_slot_content_tex, _multiples(),
            "\\arroweq{6 \\opspace \\Rightarrow \\opspace 6, 12, 18, 24}", "6",
        ),
        (
            tex_module.build_divisors_slot_content_tex, _divisors(),
            "\\arroweq{12 \\opspace \\Rightarrow \\opspace 1, 2, 3, 4, 6, 12}", "12",
        ),
        (
            tex_module.build_simplify_slot_content_tex, _simplify(),
            "\\fractionarroweq{\\frac{18}{24} \\opspace \\Rightarrow \\opspace \\frac{3}{4}}",
            "\\frac{18}{24}",
        ),
        (
            tex_module.build_frac2dec_slot_content_tex, _frac2dec(),
            "\\fractionarroweq{\\frac{3}{4} \\opspace \\Rightarrow \\opspace 0.75}",
            "\\frac{3}{4}",
        ),
        (
            tex_module.build_dec2frac_slot_content_tex, _dec2frac(),
            "\\fractionarroweq{0.6 \\opspace \\Rightarrow \\opspace \\frac{3}{5}}",
            "0.6",
        ),
        (
            tex_module.build_commondenom_slot_content_tex, _commondenom(),
            "\\fractionarroweq{\\frac{1}{3}, \\frac{1}{4} \\opspace \\Rightarrow \\opspace "
            "\\frac{4}{12}, \\frac{3}{12}}",
            "\\frac{1}{3}, \\frac{1}{4}",
        ),
    ],
)
def test_pattern_4_slot_bodies_exact(slot_format, problem, filled_body, blank_lhs) -> None:
    filled = slot_format(problem, show_answer=True)
    blank = slot_format(problem, show_answer=False)

    assert filled == filled_body
    is_fraction_variant = filled.startswith("\\fractionarroweq{")
    wrapper = "\\fractionarroweq" if is_fraction_variant else "\\arroweq"
    assert blank == f"{wrapper}{{{blank_lhs} \\opspace \\Rightarrow \\opspace {BLANK}}}"
    assert "5)" not in filled
    assert "5)" not in blank


# --- block == "n) " + slot for every pattern-4 command ------------------

@pytest.mark.parametrize(
    "block_format, slot_format, problem",
    [
        (tex_module.build_abc_block_tex, tex_module.build_abc_slot_content_tex, _abc()),
        (tex_module.build_evenodd_block_tex, tex_module.build_evenodd_slot_content_tex, _evenodd()),
        (tex_module.build_multiples_block_tex, tex_module.build_multiples_slot_content_tex, _multiples()),
        (tex_module.build_divisors_block_tex, tex_module.build_divisors_slot_content_tex, _divisors()),
        (tex_module.build_simplify_block_tex, tex_module.build_simplify_slot_content_tex, _simplify()),
        (tex_module.build_frac2dec_block_tex, tex_module.build_frac2dec_slot_content_tex, _frac2dec()),
        (tex_module.build_dec2frac_block_tex, tex_module.build_dec2frac_slot_content_tex, _dec2frac()),
        (tex_module.build_commondenom_block_tex, tex_module.build_commondenom_slot_content_tex, _commondenom()),
    ],
)
def test_pattern_4_block_is_number_prefix_plus_slot_body(block_format, slot_format, problem) -> None:
    for show_answer in (False, True):
        block = block_format(problem, show_answer)
        slot = slot_format(problem, show_answer)
        assert block == f"{problem.index}) {slot}"


@pytest.mark.parametrize(
    "block_format, slot_format, problem",
    [
        (tex_module.build_abc_block_tex, tex_module.build_abc_slot_content_tex, _abc()),
        (tex_module.build_simplify_block_tex, tex_module.build_simplify_slot_content_tex, _simplify()),
        (tex_module.build_commondenom_block_tex, tex_module.build_commondenom_slot_content_tex, _commondenom()),
    ],
)
def test_pattern_4_block_slot_equivalence_via_content_area_slot(block_format, slot_format, problem) -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)
    slot = slot_format(problem, show_answer=True)
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
    assert block_format(problem, True) == f"{problem.index}) {slot}"


# --- real-PDF spot checks (both engines, 4a / 4b / 4c) -----------------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}

_CASES = {
    "4a_abc": tex_module.build_abc_slot_content_tex,
    "4a_evenodd": tex_module.build_evenodd_slot_content_tex,
    "4a_multiples": tex_module.build_multiples_slot_content_tex,
    "4a_divisors": tex_module.build_divisors_slot_content_tex,
    "4b_simplify": tex_module.build_simplify_slot_content_tex,
    "4b_frac2dec": tex_module.build_frac2dec_slot_content_tex,
    "4b_dec2frac": tex_module.build_dec2frac_slot_content_tex,
    "4c_commondenom": tex_module.build_commondenom_slot_content_tex,
}

_CASE_PROBLEMS = {
    "4a_abc": _abc,
    "4a_evenodd": _evenodd,
    "4a_multiples": _multiples,
    "4a_divisors": _divisors,
    "4b_simplify": _simplify,
    "4b_frac2dec": _frac2dec,
    "4b_dec2frac": _dec2frac,
    "4c_commondenom": _commondenom,
}


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("case_name", sorted(_CASES))
@pytest.mark.parametrize("show_answer", [False, True])
def test_arrow_conversion_slot_compiles_to_pdf(
    engine_name: str, case_name: str, show_answer: bool, tmp_path: Path
) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    page = tex_module.PresentationPage(problems=[_CASE_PROBLEMS[case_name]()], indices=[1])
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=_CASES[case_name],
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=engine_adapter,
        show_answer=show_answer,
    )
    out_pdf_path = tmp_path / f"{engine_name}_{case_name}_{show_answer}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
