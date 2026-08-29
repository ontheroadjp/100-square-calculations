"""Tests for the shared "equation" content-format components (taxonomy
patterns 1a/1b) introduced by issue #264.

Issue #264 retrofits every pattern-1a builder (`ope` plain/tree/multi-term,
`99`, `squ`, `pi`, `lcm`/`gcd`) and pattern-1b builder (`frac`, `mixed`,
`divfrac`) so their number-free Layer-3 body is emitted through the shared
`\\horizontaleq` / `\\fractioneq` wrappers and the centralized `\\opspace`
operator gap, instead of ad hoc `$...$` / `$\\displaystyle ...$` f-strings.

Most tests here are pure-Python (assert the generated TeX string). Three
compile a real PDF via the presentation API, one per representative case
(`ope`, `frac`, blank-mode `mixed`), and run under both pdflatex and
lualatex; each is skipped when its engine binary is absent (mirroring the
skip pattern in test_nuts_calc_tex_presentation_api.py /
test_nuts_calc_tex_lualatex_engine.py).
"""

import shutil
import sys
from fractions import Fraction
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


# --- shared macro block -------------------------------------------------------

def test_content_format_macros_define_opspace_and_both_equation_wrappers() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newlength{\\opspacewidth}" in macros
    assert (
        f"\\setlength{{\\opspacewidth}}{{{tex_module.CONTENT_FORMAT_OPSPACE_WIDTH_TEX}}}"
        in macros
    )
    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{$\\displaystyle #1" in macros


def test_content_format_macros_are_spliced_into_the_legacy_document_builder() -> None:
    problems = [tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5)]
    blank, filled = tex_module.build_ope_page_pair(problems, 1, False, False)
    document = tex_module.build_document_tex(
        "A4", [blank], [filled], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert tex_module.build_content_format_macros_tex() in document
    assert document.index("\\newcommand{\\opspace}") < document.index("\\begin{document}")


def test_content_format_macros_are_spliced_into_the_presentation_document_builder() -> None:
    problems = [tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5)]
    page = tex_module.PresentationPage(problems=problems, indices=[1])
    document = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_ope_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=tex_module.ContentAreaLayout(rows=1, columns=1),
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
    )

    assert tex_module.build_content_format_macros_tex() in document
    assert document.index("\\newcommand{\\fractioneq}") < document.index("\\begin{document}")


# --- equation body helpers --------------------------------------------------

def test_build_equation_lhs_tex_interleaves_opspace_around_every_operator() -> None:
    assert tex_module.build_equation_lhs_tex(["1", "2", "3"], ["+", "\\times"]) == (
        "1 \\opspace + \\opspace 2 \\opspace \\times \\opspace 3"
    )


def test_build_equation_lhs_tex_returns_single_operand_unchanged() -> None:
    assert tex_module.build_equation_lhs_tex(["\\mathrm{LCM}(4, 6)"], []) == "\\mathrm{LCM}(4, 6)"


def test_build_horizontal_equation_tex_wraps_via_horizontaleq() -> None:
    assert tex_module.build_horizontal_equation_tex("1 \\opspace + \\opspace 2", "3") == (
        "\\horizontaleq{1 \\opspace + \\opspace 2 \\opspace = \\opspace 3}"
    )


def test_build_horizontal_equation_tex_appends_suffix_inside_the_wrapper() -> None:
    body = tex_module.build_horizontal_equation_tex(
        "17 \\opspace \\div \\opspace 5", "3", suffix_tex=" \\cdots 2"
    )
    assert body == "\\horizontaleq{17 \\opspace \\div \\opspace 5 \\opspace = \\opspace 3 \\cdots 2}"


def test_build_fraction_equation_tex_wraps_via_fractioneq() -> None:
    assert tex_module.build_fraction_equation_tex("\\frac{1}{2} \\opspace + \\opspace \\frac{1}{3}", "\\frac{5}{6}") == (
        "\\fractioneq{\\frac{1}{2} \\opspace + \\opspace \\frac{1}{3} \\opspace = \\opspace \\frac{5}{6}}"
    )


# --- pattern-1a: every slot body goes through \horizontaleq ------------------

def _tree_problem() -> tex_module.TreeOpeProblem:
    tree = tex_module.ExprTreeNode(
        operator="mul",
        left=tex_module.ExprTreeNode(
            operator="add",
            left=tex_module.ExprTreeNode(value=3),
            right=tex_module.ExprTreeNode(value=4),
        ),
        right=tex_module.ExprTreeNode(value=2),
    )
    return tex_module.TreeOpeProblem(
        index=1, operands=[3, 4, 2], operators=["mul", "add"], tree=tree, result=14
    )


PATTERN_1A_SLOT_CASES = {
    "ope": (
        lambda: tex_module.build_ope_slot_content_tex(
            tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5), True
        ),
        "\\horizontaleq{2 \\opspace + \\opspace 3 \\opspace = \\opspace 5}",
    ),
    "tree": (
        lambda: tex_module.build_tree_ope_slot_content_tex(_tree_problem(), True),
        "\\horizontaleq{(3 \\opspace + \\opspace 4) \\opspace \\times \\opspace 2 "
        "\\opspace = \\opspace 14}",
    ),
    "multi_term": (
        lambda: tex_module.build_multi_term_ope_slot_content_tex(
            tex_module.MultiTermOpeProblem(
                index=1, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=11
            ),
            True,
        ),
        "\\horizontaleq{3 \\opspace + \\opspace 4 \\opspace \\times \\opspace 2 "
        "\\opspace = \\opspace 11}",
    ),
    "kuku": (
        lambda: tex_module.build_kuku_slot_content_tex(
            tex_module.KukuProblem(index=1, a=3, b=4, c=12), True
        ),
        "\\horizontaleq{3 \\opspace \\times \\opspace 4 \\opspace = \\opspace 12}",
    ),
    "squ": (
        lambda: tex_module.build_squ_slot_content_tex(
            tex_module.SquProblem(index=1, a=3, c=9), True
        ),
        "\\horizontaleq{3 \\opspace \\times \\opspace 3 \\opspace = \\opspace 9}",
    ),
    "pi": (
        lambda: tex_module.build_pi_slot_content_tex(
            tex_module.PiProblem(index=1, a=2, c=6.28), True
        ),
        "\\horizontaleq{2 \\opspace \\times \\opspace 3.14 \\opspace = \\opspace 6.28}",
    ),
    "lcm": (
        lambda: tex_module.build_lcm_slot_content_tex(
            tex_module.NumberPairProblem(index=1, a=4, b=6, c=12), True
        ),
        "\\horizontaleq{\\mathrm{LCM}(4, 6) \\opspace = \\opspace 12}",
    ),
    "gcd": (
        lambda: tex_module.build_gcd_slot_content_tex(
            tex_module.NumberPairProblem(index=1, a=18, b=24, c=6), True
        ),
        "\\horizontaleq{\\mathrm{GCD}(18, 24) \\opspace = \\opspace 6}",
    ),
}


@pytest.mark.parametrize("name", sorted(PATTERN_1A_SLOT_CASES))
def test_pattern_1a_slot_content_uses_horizontaleq_wrapper(name: str) -> None:
    render, expected = PATTERN_1A_SLOT_CASES[name]
    body = render()
    assert body == expected
    assert body.startswith("\\horizontaleq{")
    assert "$\\displaystyle" not in body


# --- pattern-1b: every slot body goes through \fractioneq -------------------

def _fraction_problem() -> tex_module.FractionProblem:
    return tex_module.FractionProblem(
        index=1,
        a=tex_module.FractionOperand(3, 4),
        b=tex_module.FractionOperand(1, 2),
        operator="add",
        c=Fraction(5, 4),
        mixed_number_display=False,
    )


def _mixed_problem() -> tex_module.MixedProblem:
    return tex_module.MixedProblem(
        index=1,
        operands=[
            tex_module.MixedOperand("int", "2", Fraction(2), 2, 1),
            tex_module.MixedOperand("int", "3", Fraction(3), 3, 1),
        ],
        operators=["div"],
        mixed=False,
        result=Fraction(2, 3),
    )


PATTERN_1B_SLOT_CASES = {
    "frac": (
        lambda: tex_module.build_fraction_slot_content_tex(_fraction_problem(), True),
        "\\fractioneq{\\frac{3}{4} \\opspace + \\opspace \\frac{1}{2} "
        "\\opspace = \\opspace \\frac{5}{4}}",
    ),
    "mixed": (
        lambda: tex_module.build_mixed_slot_content_tex(_mixed_problem(), True),
        "\\fractioneq{2 \\opspace \\div \\opspace 3 \\opspace = \\opspace \\frac{2}{3}}",
    ),
    "divfrac": (
        lambda: tex_module.build_divfrac_slot_content_tex(
            tex_module.DivFracProblem(index=1, a=4, b=6), True
        ),
        "\\fractioneq{4 \\opspace \\div \\opspace 6 \\opspace = \\opspace \\frac{4}{6}}",
    ),
}


@pytest.mark.parametrize("name", sorted(PATTERN_1B_SLOT_CASES))
def test_pattern_1b_slot_content_uses_fractioneq_wrapper(name: str) -> None:
    render, expected = PATTERN_1B_SLOT_CASES[name]
    body = render()
    assert body == expected
    assert body.startswith("\\fractioneq{")
    assert not body.startswith("$")


# --- blank-mode geometry: blank rows differ only in the result token --------

BLANK_MODE_CASES = {
    "ope": (
        lambda sa: tex_module.build_ope_slot_content_tex(
            tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5), sa
        ),
        "5",
    ),
    "kuku": (
        lambda sa: tex_module.build_kuku_slot_content_tex(
            tex_module.KukuProblem(index=1, a=3, b=4, c=12), sa
        ),
        "12",
    ),
    "lcm": (
        lambda sa: tex_module.build_lcm_slot_content_tex(
            tex_module.NumberPairProblem(index=1, a=4, b=6, c=12), sa
        ),
        "12",
    ),
    "frac": (
        lambda sa: tex_module.build_fraction_slot_content_tex(_fraction_problem(), sa),
        "\\frac{5}{4}",
    ),
    "divfrac": (
        lambda sa: tex_module.build_divfrac_slot_content_tex(
            tex_module.DivFracProblem(index=1, a=4, b=6), sa
        ),
        "\\frac{4}{6}",
    ),
}


@pytest.mark.parametrize("name", sorted(BLANK_MODE_CASES))
def test_blank_mode_swaps_only_the_result_token_for_the_blank_marker(name: str) -> None:
    render, answer_tex = BLANK_MODE_CASES[name]
    filled = render(True)
    blank = render(False)

    assert filled.endswith(f"\\opspace = \\opspace {answer_tex}}}")
    # blank and filled share the identical wrapper + LHS + spaced `=`; only the
    # trailing result token differs (unboxed-blank consistency, guidelines item 17).
    assert blank == filled[: -len(f"{answer_tex}}}")] + f"{tex_module.BLANK_ANSWER_TEX}}}"
    assert blank.endswith(f"\\opspace = \\opspace {tex_module.BLANK_ANSWER_TEX}}}")


# --- legacy block_tex == "n) " + number-free slot body ---------------------

BLOCK_SLOT_PAIRS = {
    "ope": (
        lambda: tex_module.build_horizontal_block_tex(
            tex_module.OpeProblem(index=7, a=2, b=3, operator="add", c=5), True
        ),
        lambda: tex_module.build_ope_slot_content_tex(
            tex_module.OpeProblem(index=7, a=2, b=3, operator="add", c=5), True
        ),
    ),
    "ope_div_remainder": (
        lambda: tex_module.build_horizontal_block_tex(
            tex_module.OpeProblem(index=7, a=17, b=5, operator="div", c=3, remainder=2), False
        ),
        lambda: tex_module.build_ope_slot_content_tex(
            tex_module.OpeProblem(index=7, a=17, b=5, operator="div", c=3, remainder=2), False
        ),
    ),
    "tree": (
        lambda: tex_module.build_tree_ope_block_tex(_tree_problem_indexed(7), True),
        lambda: tex_module.build_tree_ope_slot_content_tex(_tree_problem_indexed(7), True),
    ),
    "multi_term": (
        lambda: tex_module.build_multi_term_ope_block_tex(_multi_term_indexed(7), False),
        lambda: tex_module.build_multi_term_ope_slot_content_tex(_multi_term_indexed(7), False),
    ),
    "kuku": (
        lambda: tex_module.build_kuku_block_tex(
            tex_module.KukuProblem(index=7, a=3, b=4, c=12), True, reverse=False
        ),
        lambda: tex_module.build_kuku_slot_content_tex(
            tex_module.KukuProblem(index=7, a=3, b=4, c=12), True
        ),
    ),
    "squ": (
        lambda: tex_module.build_squ_block_tex(
            tex_module.SquProblem(index=7, a=3, c=9), True, reverse=False
        ),
        lambda: tex_module.build_squ_slot_content_tex(
            tex_module.SquProblem(index=7, a=3, c=9), True
        ),
    ),
    "pi": (
        lambda: tex_module.build_pi_block_tex(
            tex_module.PiProblem(index=7, a=2, c=6.28), True, reverse=False
        ),
        lambda: tex_module.build_pi_slot_content_tex(
            tex_module.PiProblem(index=7, a=2, c=6.28), True
        ),
    ),
    "lcm": (
        lambda: tex_module.build_number_pair_block_tex(
            tex_module.NumberPairProblem(index=7, a=4, b=6, c=12), True, label="LCM"
        ),
        lambda: tex_module.build_lcm_slot_content_tex(
            tex_module.NumberPairProblem(index=7, a=4, b=6, c=12), True
        ),
    ),
    "gcd": (
        lambda: tex_module.build_number_pair_block_tex(
            tex_module.NumberPairProblem(index=7, a=18, b=24, c=6), True, label="GCD"
        ),
        lambda: tex_module.build_gcd_slot_content_tex(
            tex_module.NumberPairProblem(index=7, a=18, b=24, c=6), True
        ),
    ),
    "frac": (
        lambda: tex_module.build_fraction_block_tex(_fraction_problem_indexed(7), True),
        lambda: tex_module.build_fraction_slot_content_tex(_fraction_problem_indexed(7), True),
    ),
    "mixed": (
        lambda: tex_module.build_mixed_block_tex(_mixed_problem_indexed(7), True),
        lambda: tex_module.build_mixed_slot_content_tex(_mixed_problem_indexed(7), True),
    ),
    "divfrac": (
        lambda: tex_module.build_divfrac_block_tex(
            tex_module.DivFracProblem(index=7, a=4, b=6), True
        ),
        lambda: tex_module.build_divfrac_slot_content_tex(
            tex_module.DivFracProblem(index=7, a=4, b=6), True
        ),
    ),
}


def _tree_problem_indexed(index: int) -> tex_module.TreeOpeProblem:
    problem = _tree_problem()
    return tex_module.TreeOpeProblem(
        index=index,
        operands=problem.operands,
        operators=problem.operators,
        tree=problem.tree,
        result=problem.result,
    )


def _multi_term_indexed(index: int) -> tex_module.MultiTermOpeProblem:
    return tex_module.MultiTermOpeProblem(
        index=index, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=11
    )


def _fraction_problem_indexed(index: int) -> tex_module.FractionProblem:
    problem = _fraction_problem()
    return tex_module.FractionProblem(
        index=index,
        a=problem.a,
        b=problem.b,
        operator=problem.operator,
        c=problem.c,
        mixed_number_display=problem.mixed_number_display,
    )


def _mixed_problem_indexed(index: int) -> tex_module.MixedProblem:
    problem = _mixed_problem()
    return tex_module.MixedProblem(
        index=index,
        operands=problem.operands,
        operators=problem.operators,
        mixed=problem.mixed,
        result=problem.result,
    )


@pytest.mark.parametrize("name", sorted(BLOCK_SLOT_PAIRS))
def test_legacy_block_tex_is_number_prefix_plus_number_free_slot_body(name: str) -> None:
    build_block, build_slot = BLOCK_SLOT_PAIRS[name]
    assert build_block() == f"7) {build_slot()}"


# --- real-PDF spot checks (one per representative case, both engines) -------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


def _compile_single_slot_pdf(engine_name: str, content_format, problems, indices, tmp_path, show_answer):
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
def test_pattern_1a_ope_slot_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_ope_slot_content_tex,
        [tex_module.OpeProblem(index=1, a=128, b=64, operator="add", c=192)],
        [1],
        tmp_path,
        show_answer=True,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_pattern_1b_fraction_slot_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_fraction_slot_content_tex,
        [_fraction_problem()],
        [1],
        tmp_path,
        show_answer=True,
    )


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_pattern_1b_mixed_blank_slot_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    _compile_single_slot_pdf(
        engine_name,
        tex_module.build_mixed_slot_content_tex,
        [_mixed_problem()],
        [1],
        tmp_path,
        show_answer=False,
    )
