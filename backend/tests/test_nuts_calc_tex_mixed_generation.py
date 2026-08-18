"""
Pure-Python tests for the "mixed" (int/decimal/fraction) worksheet
generator.

Every test in this file exists to protect one invariant: no operand or
answer is ever a floating-point value or a decimal-notation display of a
non-terminating quotient -- division answers are always an exact
fractions.Fraction, rendered as a LaTeX fraction (see
nuts_calc_tex.py.md's decimal-arithmetic design note).
"""

import math
from fractions import Fraction

import pytest

import nuts_calc_tex as tex_module


def _raw_gcd(problem: tex_module.MixedProblem) -> int:
    """gcd of a two-term mul/div problem's unreduced (pre-simplification) product/quotient."""
    a, b = problem.operands
    if problem.operators[0] == "mul":
        raw_numerator = a.raw_numerator * b.raw_numerator
        raw_denominator = a.raw_denominator * b.raw_denominator
    else:
        raw_numerator = a.raw_numerator * b.raw_denominator
        raw_denominator = a.raw_denominator * b.raw_numerator
    return math.gcd(raw_numerator, raw_denominator)


@pytest.mark.parametrize("kind", ["int", "decimal", "fraction"])
def test_random_mixed_operand_produces_positive_exact_value(kind: str) -> None:
    for _ in range(50):
        operand = tex_module.random_mixed_operand(kind, 2, 2, 1)
        assert operand.kind == kind
        assert isinstance(operand.value, Fraction)
        assert operand.value > 0


@pytest.mark.parametrize("kind", ["int", "decimal", "fraction"])
def test_random_mixed_operand_populates_raw_numerator_denominator(kind: str) -> None:
    for _ in range(50):
        operand = tex_module.random_mixed_operand(kind, 2, 2, 1)
        assert operand.raw_numerator is not None
        assert operand.raw_denominator is not None
        assert Fraction(operand.raw_numerator, operand.raw_denominator) == operand.value


def test_random_mixed_operand_decimal_matches_display_string() -> None:
    for _ in range(50):
        operand = tex_module.random_mixed_operand("decimal", 2, 1, 2)
        assert operand.kind == "decimal"
        assert "." in operand.display
        whole, _, frac_part = operand.display.partition(".")
        assert len(frac_part) == 2
        assert operand.value == Fraction(int(whole + frac_part), 100)


def test_random_mixed_operand_int_has_no_decimal_point() -> None:
    for _ in range(50):
        operand = tex_module.random_mixed_operand("int", 2, 1, 1)
        assert "." not in operand.display
        assert operand.value.denominator == 1


@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_generate_mixed_problems_two_terms_exact(operator: str) -> None:
    problems = tex_module.generate_mixed_problems(
        ["int", "decimal", "fraction"], ["int", "decimal", "fraction"],
        [operator], False, 1, 1, 1, 2, 2, 40, 1,
    )
    assert len(problems) == 40
    for problem in problems:
        assert len(problem.operands) == 2
        assert problem.operators == [operator]
        a, b = problem.operands[0].value, problem.operands[1].value
        if operator == "add":
            assert a + b == problem.result
        elif operator == "sub":
            assert a - b == problem.result
            assert problem.result > 0
        elif operator == "mul":
            assert a * b == problem.result
        else:
            assert a / b == problem.result
        assert problem.result > 0


def test_generate_mixed_problems_respects_terms_range() -> None:
    problems = tex_module.generate_mixed_problems(
        ["int"], ["int"], ["add"], False, 1, 1, 1, 3, 5, 30, 1,
    )
    for problem in problems:
        assert 3 <= len(problem.operands) <= 5
        assert len(problem.operators) == len(problem.operands) - 1


def test_generate_mixed_problems_mixed_operators_uses_standard_precedence() -> None:
    problems = tex_module.generate_mixed_problems(
        ["int"], ["int"], ["mix"], True, 1, 1, 1, 3, 3, 30, 1,
    )
    for problem in problems:
        values = [operand.value for operand in problem.operands]
        expected = tex_module.evaluate_mixed_expression(
            values, problem.operators, tex_module.MIXED_STAGE_FUNCTIONS,
        )
        assert problem.result == expected


def test_generate_mixed_problems_first_term_uses_a_kinds_only() -> None:
    problems = tex_module.generate_mixed_problems(
        ["fraction"], ["int"], ["add"], False, 1, 1, 1, 2, 2, 30, 1,
    )
    for problem in problems:
        assert problem.operands[0].kind == "fraction"
        assert problem.operands[1].kind == "int"


@pytest.mark.parametrize("operator", ["mul", "div"])
def test_generate_mixed_problems_require_reducible_forces_gcd_above_one(operator: str) -> None:
    problems = tex_module.generate_mixed_problems(
        ["fraction"], ["int"], [operator], False, 1, 1, 1, 2, 2, 30, 1,
        reducible_mode="required",
    )
    assert len(problems) == 30
    for problem in problems:
        assert _raw_gcd(problem) > 1


@pytest.mark.parametrize("operator", ["mul", "div"])
def test_generate_mixed_problems_no_reducible_forces_coprime_raw_result(operator: str) -> None:
    problems = tex_module.generate_mixed_problems(
        ["int"], ["fraction"], [operator], False, 1, 1, 1, 2, 2, 30, 1,
        reducible_mode="none",
    )
    assert len(problems) == 30
    for problem in problems:
        assert _raw_gcd(problem) == 1


def test_generate_mixed_problems_mixed_reducible_covers_both_outcomes() -> None:
    problems = tex_module.generate_mixed_problems(
        ["fraction"], ["int"], ["mul"], False, 1, 1, 1, 2, 2, 30, 1,
        reducible_mode="mixed",
    )
    outcomes = {_raw_gcd(problem) > 1 for problem in problems}
    assert outcomes == {True, False}


def test_generate_mixed_problems_division_result_is_exact_fraction_not_decimal() -> None:
    # int-only 1..9 / 1..9 routinely produces non-terminating decimals
    # (e.g. 2/3); the result must stay an exact Fraction, never be coerced
    # to a float or a rounded decimal string.
    problems = tex_module.generate_mixed_problems(
        ["int"], ["int"], ["div"], False, 1, 1, 1, 2, 2, 100, 1,
    )
    for problem in problems:
        a, b = problem.operands[0].value, problem.operands[1].value
        assert problem.result == a / b
        assert isinstance(problem.result, Fraction)


def test_build_mixed_block_tex_hides_and_shows_fraction_answer() -> None:
    problem = tex_module.MixedProblem(
        index=1,
        operands=[
            tex_module.MixedOperand("int", "2", Fraction(2)),
            tex_module.MixedOperand("int", "3", Fraction(3)),
        ],
        operators=["div"], mixed=False, result=Fraction(2, 3),
    )
    blank = tex_module.build_mixed_block_tex(problem, show_answer=False)
    filled = tex_module.build_mixed_block_tex(problem, show_answer=True)
    assert "2 \\div 3" in blank
    assert r"\frac{2}{3}" not in blank
    assert r"\frac{2}{3}" in filled


def test_build_mixed_csv_rows_reports_terms_and_exact_result() -> None:
    problem = tex_module.MixedProblem(
        index=1,
        operands=[
            tex_module.MixedOperand("decimal", "0.5", Fraction(1, 2)),
            tex_module.MixedOperand("fraction", "\\frac{1}{4}", Fraction(1, 4)),
        ],
        operators=["add"], mixed=False, result=Fraction(3, 4),
    )
    assert tex_module.build_mixed_csv_rows([[problem]]) == [
        [1, 1, 2, False, "0.5 add \\frac{1}{4}", 3, 4],
    ]


def test_generate_mixed_problems_raises_when_constraints_are_unsatisfiable(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force every operand to Fraction(1): "1 sub 1" never has a positive
    # result, so every retry fails deterministically and the budget exhausts.
    def always_one(kind: str, numerator_digits: int, denominator_digits: int, decimal_places: int) -> tex_module.MixedOperand:
        return tex_module.MixedOperand("int", "1", Fraction(1))

    monkeypatch.setattr(tex_module, "random_mixed_operand", always_one)
    with pytest.raises(ValueError):
        tex_module.generate_mixed_problems(
            ["int"], ["int"], ["sub"], False, 1, 1, 1, 2, 2, 1, 1,
        )
