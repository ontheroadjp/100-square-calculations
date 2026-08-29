"""Unit tests for nuts_calc_tex.py's ContentAreaLayout abstraction (issue #184).

ContentAreaLayout is Layer 2 of #166's presentation-layer model (content-area
grid template: problem-slot count/arrangement and number-box position),
placed inside Layer 1's page shell (#182) and containing Layer 3 content
formats (#122). #184 introduces it as an additive, named unit: number
position moves from being embedded in each build_*_block_tex() output to
being owned by build_content_area_slot_tex(), without changing the existing
build_com_block_tex()/build_com_page_pair() production code path. These
tests exercise the pure-Python builders directly (no pdflatex/lualatex
required).
"""

import sys
from fractions import Fraction
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_content_area_layout_presets_match_frontend_layout_by_problem_count() -> None:
    # Mirrors frontend/web/src/presetDetail.js's LAYOUT_BY_PROBLEM_COUNT.
    expected = {
        10: (5, 2),
        20: (10, 2),
        30: (10, 3),
    }

    for problem_count, (rows, columns) in expected.items():
        layout = tex_module.CONTENT_AREA_LAYOUT_PRESETS[problem_count]
        assert layout.rows == rows
        assert layout.columns == columns


def test_content_area_layout_accepts_arbitrary_rows_and_columns() -> None:
    layout = tex_module.ContentAreaLayout(rows=7, columns=4)

    assert layout.rows == 7
    assert layout.columns == 4
    assert layout.number_box_width_mm == tex_module.CONTENT_AREA_NUMBER_BOX_WIDTH_MM


def test_build_content_area_slot_tex_places_number_box_before_content() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)

    slot_tex = tex_module.build_content_area_slot_tex(3, "$1 + 2 = 3$", layout)

    assert slot_tex == "\\makebox[8mm][l]{3)}$1 + 2 = 3$"


def test_build_content_area_slot_tex_uses_layout_number_box_width() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=12)

    slot_tex = tex_module.build_content_area_slot_tex(1, "$1 + 1 = 2$", layout)

    assert slot_tex.startswith("\\makebox[12mm][l]{1)}")


def test_build_content_area_tex_composes_one_block_per_slot_in_order() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=2)

    blocks = tex_module.build_content_area_tex(
        indices=[1, 2],
        slot_bodies=["$1 + 1 = 2$", "$2 + 2 = 4$"],
        layout=layout,
    )

    assert blocks == [
        "\\makebox[8mm][l]{1)}$1 + 1 = 2$",
        "\\makebox[8mm][l]{2)}$2 + 2 = 4$",
    ]


def test_build_com_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.ComProblem(index=5, a=3, c=4, target=7)

    content_tex = tex_module.build_com_slot_content_tex(problem, show_answer=True)

    assert content_tex == "\\boxedblankeq{3 \\opspace + \\opspace 4 \\opspace = \\opspace 7}"
    assert "5)" not in content_tex


def test_build_com_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_com_block_tex() output byte-for-byte, so
    Layer 2 can be adopted without a visual regression."""
    problem = tex_module.ComProblem(index=5, a=3, c=4, target=7)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_com_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_com_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_ope_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.OpeProblem(index=5, a=3, b=4, operator="add", c=7)

    content_tex = tex_module.build_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{3 \\opspace + \\opspace 4 \\opspace = \\opspace 7}"
    )
    assert "5)" not in content_tex


def test_build_fraction_slot_content_tex_omits_problem_number_and_preserves_display() -> None:
    problem = tex_module.FractionProblem(
        index=5,
        a=tex_module.FractionOperand(3, 4),
        b=tex_module.FractionOperand(1, 2),
        operator="add",
        c=tex_module.Fraction(5, 4),
        mixed_number_display=False,
    )

    content_tex = tex_module.build_fraction_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\fractioneq{\\frac{3}{4} \\opspace + \\opspace \\frac{1}{2} "
        "\\opspace = \\opspace \\frac{5}{4}}"
    )
    assert "5)" not in content_tex


def test_build_fraction_slot_content_tex_matches_block_body_and_blank_output() -> None:
    problem = tex_module.FractionProblem(
        index=5,
        a=tex_module.FractionOperand(2, 5, whole=1),
        b=tex_module.FractionOperand(1, 5),
        operator="sub",
        c=tex_module.Fraction(6, 5),
        mixed_number_display=True,
    )

    filled_content = tex_module.build_fraction_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_fraction_slot_content_tex(problem, show_answer=False)

    assert tex_module.build_fraction_block_tex(problem, True) == f"{problem.index}) {filled_content}"
    assert filled_content == (
        "\\fractioneq{1\\frac{2}{5} \\opspace - \\opspace \\frac{1}{5} "
        "\\opspace = \\opspace 1\\frac{1}{5}}"
    )
    assert blank_content.endswith(f"\\opspace = \\opspace {tex_module.BLANK_ANSWER_TEX}}}")


def test_build_simplify_slot_content_tex_omits_number_and_renders_answers() -> None:
    problem = tex_module.SimplifyProblem(
        index=5,
        operand=tex_module.FractionOperand(18, 24),
        reduced=Fraction(3, 4),
    )

    filled_content = tex_module.build_simplify_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_simplify_slot_content_tex(problem, show_answer=False)

    assert filled_content == (
        "\\fractionarroweq{\\frac{18}{24} \\opspace \\Rightarrow \\opspace \\frac{3}{4}}"
    )
    assert "5)" not in filled_content
    assert blank_content == (
        f"\\fractionarroweq{{\\frac{{18}}{{24}} \\opspace \\Rightarrow \\opspace {tex_module.BLANK_ANSWER_TEX}}}"
    )


def test_build_simplify_slot_content_tex_reconstructs_legacy_block_body() -> None:
    problem = tex_module.SimplifyProblem(
        index=5,
        operand=tex_module.FractionOperand(18, 24),
        reduced=Fraction(3, 4),
    )
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot_content_tex = tex_module.build_simplify_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert tex_module.build_simplify_block_tex(problem, True) == (
        f"{problem.index}) {slot_content_tex}"
    )


def test_build_frac2dec_slot_content_tex_omits_number_and_renders_answers() -> None:
    problem = tex_module.Frac2DecProblem(
        index=5,
        operand=tex_module.FractionOperand(3, 4),
        decimal_places=2,
        scaled_numerator=75,
    )

    filled_content = tex_module.build_frac2dec_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_frac2dec_slot_content_tex(problem, show_answer=False)

    assert filled_content == (
        "\\fractionarroweq{\\frac{3}{4} \\opspace \\Rightarrow \\opspace 0.75}"
    )
    assert "5)" not in filled_content
    assert blank_content == (
        f"\\fractionarroweq{{\\frac{{3}}{{4}} \\opspace \\Rightarrow \\opspace {tex_module.BLANK_ANSWER_TEX}}}"
    )


def test_build_frac2dec_slot_content_tex_reconstructs_legacy_block_body() -> None:
    problem = tex_module.Frac2DecProblem(
        index=5,
        operand=tex_module.FractionOperand(3, 4),
        decimal_places=2,
        scaled_numerator=75,
    )
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot_content_tex = tex_module.build_frac2dec_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert tex_module.build_frac2dec_block_tex(problem, True) == (
        f"{problem.index}) {slot_content_tex}"
    )


def test_build_dec2frac_slot_content_tex_omits_number_and_renders_answers() -> None:
    problem = tex_module.Dec2FracProblem(
        index=5,
        decimal_places=1,
        scaled_numerator=6,
        reduced=Fraction(3, 5),
    )

    filled_content = tex_module.build_dec2frac_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_dec2frac_slot_content_tex(problem, show_answer=False)

    assert filled_content == (
        "\\fractionarroweq{0.6 \\opspace \\Rightarrow \\opspace \\frac{3}{5}}"
    )
    assert "5)" not in filled_content
    assert blank_content.endswith(
        f"\\Rightarrow \\opspace {tex_module.BLANK_ANSWER_TEX}}}"
    )


def test_build_dec2frac_slot_content_tex_reconstructs_legacy_block_body() -> None:
    problem = tex_module.Dec2FracProblem(
        index=5,
        decimal_places=1,
        scaled_numerator=6,
        reduced=Fraction(3, 5),
    )
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot_content_tex = tex_module.build_dec2frac_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert tex_module.build_dec2frac_block_tex(problem, True) == (
        f"{problem.index}) {slot_content_tex}"
    )


def test_build_fraction_comparison_slot_content_tex_omits_number_and_renders_answers() -> None:
    problem = tex_module.FractionComparisonProblem(
        index=5,
        a=tex_module.FractionComparisonOperand(1, 2),
        b=tex_module.FractionComparisonOperand(2, 3),
    )

    filled_content = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=False)

    # issue #266: pattern 3 emits via the shared \compareeq/\opspace components;
    # both operands here are \frac, so neither is \vcenter-wrapped.
    assert filled_content == r"\compareeq{\frac{1}{2} \opspace < \opspace \frac{2}{3}}"
    assert "5)" not in filled_content
    assert blank_content == (
        r"\compareeq{\frac{1}{2} \opspace \boxedblank \opspace \frac{2}{3}}"
    )


def test_build_fraction_comparison_slot_content_tex_reconstructs_legacy_block_body() -> None:
    problem = tex_module.FractionComparisonProblem(
        index=5,
        a=tex_module.FractionComparisonOperand(1, 2),
        b=tex_module.FractionComparisonOperand(2, 3),
    )
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot_content_tex = tex_module.build_fraction_comparison_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert tex_module.build_fraction_comparison_block_tex(problem, True) == (
        f"{problem.index}) {slot_content_tex}"
    )


def _commondenom_problem() -> "tex_module.CommonDenomProblem":
    return tex_module.CommonDenomProblem(
        index=5,
        a=tex_module.FractionOperand(1, 3),
        b=tex_module.FractionOperand(1, 4),
        a_converted=tex_module.FractionOperand(4, 12),
        b_converted=tex_module.FractionOperand(3, 12),
    )


def test_build_commondenom_slot_content_tex_omits_number_and_renders_answers() -> None:
    problem = _commondenom_problem()

    filled_content = tex_module.build_commondenom_slot_content_tex(problem, show_answer=True)
    blank_content = tex_module.build_commondenom_slot_content_tex(problem, show_answer=False)

    assert filled_content == (
        "\\fractionarroweq{\\frac{1}{3}, \\frac{1}{4} \\opspace \\Rightarrow \\opspace "
        "\\frac{4}{12}, \\frac{3}{12}}"
    )
    assert "5)" not in filled_content
    assert blank_content == (
        f"\\fractionarroweq{{\\frac{{1}}{{3}}, \\frac{{1}}{{4}} \\opspace \\Rightarrow \\opspace "
        f"{tex_module.BLANK_ANSWER_TEX}}}"
    )


def test_build_commondenom_slot_content_tex_reconstructs_legacy_block_body() -> None:
    problem = _commondenom_problem()
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    slot_content_tex = tex_module.build_commondenom_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert tex_module.build_commondenom_block_tex(problem, True) == (
        f"{problem.index}) {slot_content_tex}"
    )


def test_build_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_horizontal_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #205), so Layer 2 can be adopted
    without a visual regression."""
    problem = tex_module.OpeProblem(index=5, a=3, b=4, operator="add", c=7)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_kuku_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.KukuProblem(index=5, a=3, b=4, c=12)

    content_tex = tex_module.build_kuku_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{3 \\opspace \\times \\opspace 4 \\opspace = \\opspace 12}"
    )
    assert "5)" not in content_tex


def test_build_kuku_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_kuku_block_tex() non-reverse output
    byte-for-byte (issue #208), so Layer 2 can be adopted without a visual
    regression."""
    problem = tex_module.KukuProblem(index=5, a=3, b=4, c=12)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_kuku_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_kuku_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_pi_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.PiProblem(index=5, a=3, c=9.42)

    content_tex = tex_module.build_pi_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{3 \\opspace \\times \\opspace 3.14 \\opspace = \\opspace 9.42}"
    )
    assert "5)" not in content_tex


def test_build_pi_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_pi_block_tex() non-reverse output
    byte-for-byte (content-format pattern 1a, issue #210), so Layer 2 can be
    adopted without a visual regression."""
    problem = tex_module.PiProblem(index=5, a=3, c=9.42)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_pi_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_pi_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def _make_tree_ope_problem(index: int) -> "tex_module.TreeOpeProblem":
    # (3 + 4) x 2 = 14
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
        index=index, operands=[3, 4, 2], operators=["mul", "add"], tree=tree, result=14,
    )


def test_build_tree_ope_slot_content_tex_omits_problem_number() -> None:
    problem = _make_tree_ope_problem(index=5)

    content_tex = tex_module.build_tree_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{(3 \\opspace + \\opspace 4) \\opspace \\times \\opspace 2 "
        "\\opspace = \\opspace 14}"
    )
    assert "5)" not in content_tex


def test_build_tree_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_tree_ope_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #206), so Layer 2 can be adopted
    without a visual regression."""
    problem = _make_tree_ope_problem(index=5)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_tree_ope_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_tree_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_multi_term_ope_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.MultiTermOpeProblem(
        index=5, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=14,
    )

    content_tex = tex_module.build_multi_term_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{3 \\opspace + \\opspace 4 \\opspace \\times \\opspace 2 "
        "\\opspace = \\opspace 14}"
    )
    assert "5)" not in content_tex


def test_build_multi_term_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_multi_term_ope_block_tex() output
    byte-for-byte (content-format pattern 1a, issue #207), so Layer 2 can be
    adopted without a visual regression."""
    problem = tex_module.MultiTermOpeProblem(
        index=5, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=14,
    )
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_multi_term_ope_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_multi_term_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_missing_value_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.MissingValueProblem(
        index=5, a=8, b=2, operator="add", c=10, blank="b",
    )

    blank_tex = tex_module.build_missing_value_slot_content_tex(problem, show_answer=False)
    filled_tex = tex_module.build_missing_value_slot_content_tex(problem, show_answer=True)

    assert blank_tex == (
        "\\boxedblankeq{8 \\opspace + \\opspace "
        f"{tex_module.BOXED_BLANK_OPERAND_TEX} \\opspace = \\opspace 10}}"
    )
    assert filled_tex == "\\boxedblankeq{8 \\opspace + \\opspace 2 \\opspace = \\opspace 10}"
    assert "5)" not in blank_tex


def test_build_missing_value_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_missing_value_block_tex() output
    byte-for-byte (content-format pattern 2, issue #223), so Layer 2 can be
    adopted without a visual regression -- for both the blanked-a and
    blanked-b operand positions and both the blank and filled variants."""
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    for blank in tex_module.MISSING_VALUE_POSITIONS:
        problem = tex_module.MissingValueProblem(
            index=5, a=8, b=2, operator="add", c=10, blank=blank,
        )
        for show_answer in (False, True):
            original_tex = tex_module.build_missing_value_block_tex(problem, show_answer=show_answer)
            slot_content_tex = tex_module.build_missing_value_slot_content_tex(
                problem, show_answer=show_answer
            )
            composed_tex = tex_module.build_content_area_slot_tex(
                problem.index, slot_content_tex, layout
            )

            assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
            assert original_tex == f"{problem.index}) {slot_content_tex}"


def _make_mixed_problem(index: int) -> "tex_module.MixedProblem":
    return tex_module.MixedProblem(
        index=index,
        operands=[
            tex_module.MixedOperand("int", "3", Fraction(3)),
            tex_module.MixedOperand("decimal", "0.5", Fraction(1, 2)),
            tex_module.MixedOperand("fraction", "\\frac{2}{3}", Fraction(2, 3)),
        ],
        operators=["mul", "add"],
        mixed=True,
        result=Fraction(13, 6),
    )


def test_build_mixed_slot_content_tex_omits_problem_number_and_preserves_body() -> None:
    problem = _make_mixed_problem(index=5)

    content_tex = tex_module.build_mixed_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\fractioneq{3 \\opspace \\times \\opspace 0.5 \\opspace + \\opspace "
        "\\frac{2}{3} \\opspace = \\opspace \\frac{13}{6}}"
    )
    assert "5)" not in content_tex


def test_build_mixed_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = _make_mixed_problem(index=5)
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    original_tex = tex_module.build_mixed_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_mixed_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_mixed_slot_content_tex_renders_blank_answer() -> None:
    problem = _make_mixed_problem(index=5)

    content_tex = tex_module.build_mixed_slot_content_tex(problem, show_answer=False)

    assert content_tex.endswith(f"\\opspace = \\opspace {tex_module.BLANK_ANSWER_TEX}}}")


def test_build_divfrac_slot_content_tex_omits_number_and_preserves_unreduced_answer() -> None:
    problem = tex_module.DivFracProblem(index=5, a=4, b=6)

    content_tex = tex_module.build_divfrac_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\fractioneq{4 \\opspace \\div \\opspace 6 \\opspace = \\opspace \\frac{4}{6}}"
    )
    assert "5)" not in content_tex


def test_build_divfrac_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = tex_module.DivFracProblem(index=5, a=4, b=6)
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=0)

    original_tex = tex_module.build_divfrac_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_divfrac_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_divfrac_slot_content_tex_renders_blank_answer() -> None:
    problem = tex_module.DivFracProblem(index=5, a=4, b=6)

    content_tex = tex_module.build_divfrac_slot_content_tex(problem, show_answer=False)

    assert content_tex == (
        "\\fractioneq{4 \\opspace \\div \\opspace 6 \\opspace = \\opspace "
        f"{tex_module.BLANK_ANSWER_TEX}}}"
    )


def test_build_lcm_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.NumberPairProblem(index=5, a=4, b=6, c=12)

    content_tex = tex_module.build_lcm_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{\\mathrm{LCM}(4, 6) \\opspace = \\opspace 12}"
    )
    assert "5)" not in content_tex


def test_build_lcm_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_number_pair_block_tex(..., label='LCM')
    output byte-for-byte (issue #211), so Layer 2 can be adopted without a
    visual regression."""
    problem = tex_module.NumberPairProblem(index=5, a=4, b=6, c=12)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_number_pair_block_tex(problem, show_answer=True, label="LCM")
    slot_content_tex = tex_module.build_lcm_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_gcd_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.NumberPairProblem(index=5, a=18, b=24, c=6)

    content_tex = tex_module.build_gcd_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{\\mathrm{GCD}(18, 24) \\opspace = \\opspace 6}"
    )
    assert "5)" not in content_tex


def test_build_gcd_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing GCD number-pair block body byte-for-byte (content-
    format pattern 1a, issue #212), so Layer 2 can be adopted without a visual
    regression."""
    problem = tex_module.NumberPairProblem(index=5, a=18, b=24, c=6)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_number_pair_block_tex(
        problem, show_answer=True, label="GCD"
    )
    slot_content_tex = tex_module.build_gcd_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_evenodd_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.EvenOddProblem(index=5, a=4, is_even=True)

    content_tex = tex_module.build_evenodd_slot_content_tex(problem, show_answer=True)

    assert content_tex == "\\arroweq{4 \\opspace \\Rightarrow \\opspace \\mathrm{even}}"
    assert "5)" not in content_tex


def test_build_evenodd_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """The Layer-3 body must preserve the existing even/odd TeX output."""
    problem = tex_module.EvenOddProblem(index=5, a=3, is_even=False)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_evenodd_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_evenodd_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_squ_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.SquProblem(index=5, a=3, c=9)

    content_tex = tex_module.build_squ_slot_content_tex(problem, show_answer=True)

    assert content_tex == (
        "\\horizontaleq{3 \\opspace \\times \\opspace 3 \\opspace = \\opspace 9}"
    )
    assert "5)" not in content_tex


def test_build_squ_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_squ_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #209), so Layer 2 can be adopted
    without a visual regression. Only the non-reversed form is covered
    (basic-case scope, matching #199's `com` precedent)."""
    problem = tex_module.SquProblem(index=5, a=3, c=9)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_squ_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_squ_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_multiples_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.MultiplesProblem(index=5, a=6, multiples=[6, 12, 18, 24])

    content_tex = tex_module.build_multiples_slot_content_tex(problem, show_answer=True)

    assert content_tex == "\\arroweq{6 \\opspace \\Rightarrow \\opspace 6, 12, 18, 24}"
    assert "5)" not in content_tex


def test_build_multiples_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = tex_module.MultiplesProblem(index=5, a=6, multiples=[6, 12, 18, 24, 30])
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_multiples_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_multiples_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"
    assert tex_module.build_multiples_slot_content_tex(
        problem, show_answer=False
    ) == f"\\arroweq{{6 \\opspace \\Rightarrow \\opspace {tex_module.BLANK_ANSWER_TEX}}}"


def test_build_divisors_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.DivisorsProblem(index=5, a=12, divisors=[1, 2, 3, 4, 6, 12])

    content_tex = tex_module.build_divisors_slot_content_tex(problem, show_answer=True)

    assert content_tex == "\\arroweq{12 \\opspace \\Rightarrow \\opspace 1, 2, 3, 4, 6, 12}"
    assert "5)" not in content_tex


def test_build_divisors_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = tex_module.DivisorsProblem(index=5, a=12, divisors=[1, 2, 3, 4, 6, 12])
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_divisors_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_divisors_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"
    assert tex_module.build_divisors_slot_content_tex(
        problem, show_answer=False
    ) == f"\\arroweq{{12 \\opspace \\Rightarrow \\opspace {tex_module.BLANK_ANSWER_TEX}}}"


def test_content_area_layout_defaults_to_numbered() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)

    assert layout.numbered is True


def test_build_hundred_square_slot_content_tex_ports_block_tex_as_is() -> None:
    """Issue #229: the `100` Layer-3 content format is build_hundred_square_block_tex
    verbatim -- the grid already carries no per-problem number prefix, so no
    number needs stripping and the existing visuals are preserved as-is."""
    table = tex_module.HundredSquareTable(
        left_values=list(range(1, 11)), top_values=list(range(1, 11))
    )

    for show_answer in (False, True):
        slot_content_tex = tex_module.build_hundred_square_slot_content_tex(
            table, show_answer=show_answer
        )

        assert slot_content_tex == tex_module.build_hundred_square_block_tex(
            table, show_answer=show_answer
        )
        assert "makebox" not in slot_content_tex
