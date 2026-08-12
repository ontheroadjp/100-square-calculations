"""Pure-Python tests for the LaTeX fraction worksheet generator."""

from fractions import Fraction

import pytest

import nuts_calc_tex as tex_module


@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_generate_fraction_problems_calculates_exact_answers(operator: str) -> None:
    problems = tex_module.generate_fraction_problems(
        1, 1, [operator], 20, 1, False, True, False,
    )

    assert len(problems) == 20
    for problem in problems:
        assert problem.c == tex_module.calculate_fraction(
            problem.a.value, problem.b.value, operator,
        )
        assert problem.c > 0


def test_generate_fraction_problems_preserves_common_denominators() -> None:
    problems = tex_module.generate_fraction_problems(
        1, 1, ["add", "sub"], 20, 1, True, True, True,
    )

    for problem in problems:
        assert problem.a.denominator == problem.b.denominator
        assert problem.a.value < 1
        assert problem.b.value < 1
        assert 0 < problem.c < 1


def test_generate_fraction_problems_expands_mix_per_problem() -> None:
    problems = tex_module.generate_fraction_problems(
        1, 1, ["mix"], 50, 1, False, True, False,
    )
    assert {problem.operator for problem in problems} <= set(tex_module.MIX_OPERATORS)
    assert all(problem.operator != "mix" for problem in problems)


def test_generate_fraction_problems_requires_different_denominators() -> None:
    problems = tex_module.generate_fraction_problems(
        1, 1, ["add", "sub"], 30, 1, False, True, False, True,
    )
    assert all(problem.a.denominator != problem.b.denominator for problem in problems)


def test_fraction_to_tex_reduces_exact_answers_but_preserves_operands() -> None:
    operand = tex_module.FractionOperand(2, 4)
    assert tex_module.fraction_to_tex(operand) == r"\frac{2}{4}"
    assert tex_module.fraction_to_tex(Fraction(2, 4)) == r"\frac{1}{2}"


def test_build_fraction_block_tex_hides_and_shows_answer() -> None:
    problem = tex_module.FractionProblem(
        1, tex_module.FractionOperand(1, 2), tex_module.FractionOperand(1, 3),
        "add", Fraction(5, 6),
    )
    blank = tex_module.build_fraction_block_tex(problem, False)
    filled = tex_module.build_fraction_block_tex(problem, True)
    assert r"\frac{5}{6}" not in blank
    assert r"\frac{1}{2} + \frac{1}{3}" in blank
    assert r"\frac{5}{6}" in filled


def test_build_fraction_csv_rows_keeps_operands_and_reduced_answer() -> None:
    problem = tex_module.FractionProblem(
        1, tex_module.FractionOperand(2, 4), tex_module.FractionOperand(1, 4),
        "add", Fraction(3, 4),
    )
    assert tex_module.build_fraction_csv_rows([[problem]]) == [
        [1, 1, 2, 4, "add", 1, 4, 3, 4],
    ]


@pytest.mark.parametrize(
    ("pattern", "a_form", "b_form"),
    [
        ("same-denominator", "proper", "proper"),
        ("same-numerator", "proper", "proper"),
        ("different-denominators", "proper", "proper"),
        ("different-denominators", "mixed", "proper"),
        ("different-denominators", "improper", "mixed"),
        ("different-denominators", "mix", "mix"),
    ],
)
def test_generate_fraction_comparison_problems_matches_pattern_and_forms(
        pattern: str, a_form: str, b_form: str,
    ) -> None:
    problems = tex_module.generate_fraction_comparison_problems(
        pattern, a_form, b_form, 1, 1, 30, 1,
    )

    assert len(problems) == 30
    for problem in problems:
        assert problem.a.value != problem.b.value
        assert problem.relation in ("<", ">")
        if pattern == "same-denominator":
            assert problem.a.denominator == problem.b.denominator
            assert problem.a.numerator != problem.b.numerator
        elif pattern == "same-numerator":
            assert problem.a.numerator == problem.b.numerator
            assert problem.a.denominator != problem.b.denominator
        else:
            assert problem.a.denominator != problem.b.denominator


def test_comparison_tex_uses_box_for_question_and_relation_for_answer() -> None:
    problem = tex_module.FractionComparisonProblem(
        1,
        tex_module.FractionComparisonOperand(1, 2),
        tex_module.FractionComparisonOperand(1, 3, 2),
    )
    blank = tex_module.build_fraction_comparison_block_tex(problem, False)
    filled = tex_module.build_fraction_comparison_block_tex(problem, True)

    assert tex_module.BOXED_BLANK_TEX in blank
    assert r"2\frac{1}{3}" in blank
    assert " < " in filled


def test_comparison_csv_rows_include_displayed_operands_and_relation() -> None:
    problem = tex_module.FractionComparisonProblem(
        1,
        tex_module.FractionComparisonOperand(3, 2),
        tex_module.FractionComparisonOperand(1, 2, 1),
    )
    assert tex_module.build_fraction_comparison_csv_rows([[problem]]) == [
        [1, 1, 0, 3, 2, ">", 1, 1, 2],
    ]
