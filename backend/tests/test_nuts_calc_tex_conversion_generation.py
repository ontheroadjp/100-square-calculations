"""Unit tests for nuts_calc_tex.py's fraction/decimal conversion drill
problem-generation logic (issue #96): `simplify`, `commondenom`,
`frac2dec`, `dec2frac`, `divfrac`.

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import math
import sys
from fractions import Fraction
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


# --- simplify ---------------------------------------------------------

def test_generate_simplify_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_simplify_problems(2, 2, order=10, start_index=6)
    assert [problem.index for problem in problems] == list(range(6, 16))


def test_generate_simplify_problems_are_always_reducible_and_correctly_reduced() -> None:
    problems = tex_module.generate_simplify_problems(2, 2, order=30, start_index=1)
    for problem in problems:
        assert math.gcd(problem.operand.numerator, problem.operand.denominator) > 1
        assert problem.reduced == Fraction(problem.operand.numerator, problem.operand.denominator)


def test_build_simplify_block_tex_blank_hides_answer() -> None:
    problem = tex_module.SimplifyProblem(
        index=1, operand=tex_module.FractionOperand(18, 24), reduced=Fraction(3, 4),
    )
    blank_tex = tex_module.build_simplify_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_simplify_block_tex(problem, show_answer=True)
    assert '\\frac{3}{4}' not in blank_tex
    assert '\\frac{18}{24} \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '\\frac{18}{24} \\Rightarrow \\frac{3}{4}$' in filled_tex


def test_build_simplify_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.SimplifyProblem(index=1, operand=tex_module.FractionOperand(18, 24), reduced=Fraction(3, 4)),
        tex_module.SimplifyProblem(index=2, operand=tex_module.FractionOperand(4, 6), reduced=Fraction(2, 3)),
    ]
    assert tex_module.build_simplify_bottom_answer_tex(problems) == (
        '(1) $\\displaystyle \\frac{3}{4}$ \\quad (2) $\\displaystyle \\frac{2}{3}$'
    )


def test_build_simplify_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.SimplifyProblem(index=1, operand=tex_module.FractionOperand(18, 24), reduced=Fraction(3, 4))]
    rows = tex_module.build_simplify_csv_rows([page1])
    assert rows == [[1, 1, 18, 24, 3, 4]]


# --- commondenom --------------------------------------------------------

def test_generate_commondenom_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_commondenom_problems(1, 1, order=10, start_index=3)
    assert [problem.index for problem in problems] == list(range(3, 13))


def test_generate_commondenom_problems_have_different_input_denominators() -> None:
    problems = tex_module.generate_commondenom_problems(1, 1, order=30, start_index=1)
    for problem in problems:
        assert problem.a.denominator != problem.b.denominator


def test_generate_commondenom_problems_converted_values_match_originals() -> None:
    problems = tex_module.generate_commondenom_problems(2, 2, order=30, start_index=1)
    for problem in problems:
        assert problem.a_converted.denominator == problem.b_converted.denominator
        assert Fraction(problem.a_converted.numerator, problem.a_converted.denominator) == problem.a.value
        assert Fraction(problem.b_converted.numerator, problem.b_converted.denominator) == problem.b.value


def test_build_commondenom_block_tex_blank_hides_answer() -> None:
    problem = tex_module.CommonDenomProblem(
        index=1,
        a=tex_module.FractionOperand(1, 3), b=tex_module.FractionOperand(1, 4),
        a_converted=tex_module.FractionOperand(4, 12), b_converted=tex_module.FractionOperand(3, 12),
    )
    blank_tex = tex_module.build_commondenom_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_commondenom_block_tex(problem, show_answer=True)
    assert '\\frac{4}{12}' not in blank_tex
    assert '\\frac{1}{3}, \\frac{1}{4} \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '\\frac{1}{3}, \\frac{1}{4} \\Rightarrow \\frac{4}{12}, \\frac{3}{12}$' in filled_tex


def test_build_commondenom_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.CommonDenomProblem(
        index=1,
        a=tex_module.FractionOperand(1, 3), b=tex_module.FractionOperand(1, 4),
        a_converted=tex_module.FractionOperand(4, 12), b_converted=tex_module.FractionOperand(3, 12),
    )]
    rows = tex_module.build_commondenom_csv_rows([page1])
    assert rows == [[1, 1, 1, 3, 1, 4, 4, 12, 3, 12]]


# --- frac2dec -------------------------------------------------------------

def test_denominator_decimal_places_returns_none_for_non_terminating_denominator() -> None:
    assert tex_module.denominator_decimal_places(3) is None
    assert tex_module.denominator_decimal_places(7) is None


def test_denominator_decimal_places_returns_max_factor_count() -> None:
    assert tex_module.denominator_decimal_places(2) == 1
    assert tex_module.denominator_decimal_places(4) == 2
    assert tex_module.denominator_decimal_places(5) == 1
    assert tex_module.denominator_decimal_places(8) == 3
    assert tex_module.denominator_decimal_places(20) == 2


def test_terminating_denominators_excludes_non_terminating_values() -> None:
    candidates = tex_module.terminating_denominators(2, 9)
    assert candidates == [2, 4, 5, 8]


def test_generate_frac2dec_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_frac2dec_problems(1, 1, order=10, start_index=4)
    assert [problem.index for problem in problems] == list(range(4, 14))


def test_generate_frac2dec_problems_decimal_matches_fraction_exactly() -> None:
    problems = tex_module.generate_frac2dec_problems(2, 2, order=30, start_index=1)
    for problem in problems:
        expected = Fraction(problem.operand.numerator, problem.operand.denominator)
        actual = Fraction(problem.scaled_numerator, 10 ** problem.decimal_places)
        assert actual == expected


def test_build_frac2dec_block_tex_blank_hides_answer() -> None:
    problem = tex_module.Frac2DecProblem(
        index=1, operand=tex_module.FractionOperand(3, 4), decimal_places=2, scaled_numerator=75,
    )
    blank_tex = tex_module.build_frac2dec_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_frac2dec_block_tex(problem, show_answer=True)
    assert '0.75' not in blank_tex
    assert '\\frac{3}{4} \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '\\frac{3}{4} \\Rightarrow 0.75$' in filled_tex


def test_build_frac2dec_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.Frac2DecProblem(
        index=1, operand=tex_module.FractionOperand(3, 4), decimal_places=2, scaled_numerator=75,
    )]
    rows = tex_module.build_frac2dec_csv_rows([page1])
    assert rows == [[1, 1, 3, 4, '0.75']]


# --- dec2frac -------------------------------------------------------------

def test_generate_dec2frac_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_dec2frac_problems(order=10, start_index=2)
    assert [problem.index for problem in problems] == list(range(2, 12))


def test_generate_dec2frac_problems_reduced_matches_decimal_and_has_nontrivial_denominator() -> None:
    problems = tex_module.generate_dec2frac_problems(order=30, start_index=1)
    for problem in problems:
        assert problem.reduced == Fraction(problem.scaled_numerator, 10 ** problem.decimal_places)
        assert problem.reduced.denominator > 1


def test_build_dec2frac_block_tex_blank_hides_answer() -> None:
    problem = tex_module.Dec2FracProblem(index=1, decimal_places=1, scaled_numerator=6, reduced=Fraction(3, 5))
    blank_tex = tex_module.build_dec2frac_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_dec2frac_block_tex(problem, show_answer=True)
    assert '\\frac{3}{5}' not in blank_tex
    assert '0.6 \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '0.6 \\Rightarrow \\frac{3}{5}$' in filled_tex


def test_build_dec2frac_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.Dec2FracProblem(index=1, decimal_places=1, scaled_numerator=6, reduced=Fraction(3, 5))]
    rows = tex_module.build_dec2frac_csv_rows([page1])
    assert rows == [[1, 1, '0.6', 3, 5]]


# --- divfrac ----------------------------------------------------------

def test_generate_divfrac_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_divfrac_problems(list(range(1, 10)), list(range(1, 10)), order=10, start_index=5)
    assert [problem.index for problem in problems] == list(range(5, 15))


def test_generate_divfrac_problems_operand_matches_a_and_b() -> None:
    problems = tex_module.generate_divfrac_problems(list(range(1, 10)), list(range(1, 10)), order=20, start_index=1)
    for problem in problems:
        assert problem.operand.numerator == problem.a
        assert problem.operand.denominator == problem.b


def test_build_divfrac_block_tex_does_not_reduce_answer() -> None:
    problem = tex_module.DivFracProblem(index=1, a=2, b=4)
    blank_tex = tex_module.build_divfrac_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_divfrac_block_tex(problem, show_answer=True)
    assert '\\frac{2}{4}' not in blank_tex
    assert '2 \\div 4 = \\hspace{1.5em}$' in blank_tex
    assert '2 \\div 4 = \\frac{2}{4}$' in filled_tex
    assert '\\frac{1}{2}' not in filled_tex


def test_build_divfrac_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.DivFracProblem(index=1, a=2, b=3)]
    rows = tex_module.build_divfrac_csv_rows([page1])
    assert rows == [[1, 1, 2, 3]]
