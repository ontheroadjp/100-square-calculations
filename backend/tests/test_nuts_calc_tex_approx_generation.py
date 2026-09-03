"""Unit tests for nuts_calc_tex.py's `approx` (概数 rounding / estimation)
drill logic (issue #346): the pure rounding primitives, resolve_approx_params
validation / default-filling, generate_approx_problems for all three kinds,
and the block / bottom-answer / CSV renderers.

These exercise the pure-Python functions directly (no pdflatex required),
complementing the pdflatex-gated end-to-end tests in test_nuts_calc_tex.py.
"""

import random
import sys
from fractions import Fraction
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


# --- rounding primitives ------------------------------------------------

def test_approx_round_to_place_four_five_rounding() -> None:
    assert tex_module._approx_round_to_place(38472, 3, 'round') == 38000
    assert tex_module._approx_round_to_place(38572, 3, 'round') == 39000
    assert tex_module._approx_round_to_place(38500, 3, 'round') == 39000  # half rounds up


def test_approx_round_to_place_up_and_down() -> None:
    assert tex_module._approx_round_to_place(38472, 3, 'up') == 39000
    assert tex_module._approx_round_to_place(38472, 3, 'down') == 38000
    assert tex_module._approx_round_to_place(38000, 3, 'up') == 38000  # exact multiple never bumps


def test_approx_round_value_by_significant_digits() -> None:
    assert tex_module._approx_round_value(38472, 'round', 2, None) == 38000
    assert tex_module._approx_round_value(38472, 'round', 1, None) == 40000
    # A value with no more digits than sig_digits is returned unchanged.
    assert tex_module._approx_round_value(47, 'round', 3, None) == 47


def test_approx_round_value_prefers_explicit_round_place() -> None:
    assert tex_module._approx_round_value(38472, 'round', None, 2) == 38500


def test_round_half_up_fraction_matches_four_five_rule() -> None:
    assert tex_module.round_half_up_fraction(Fraction(58, 70), 2, 'round') == 83  # 0.8285... -> 0.83
    assert tex_module.round_half_up_fraction(Fraction(1, 8), 2, 'round') == 13    # 0.125 -> 0.13 (half up)
    assert tex_module.round_half_up_fraction(Fraction(1, 8), 2, 'down') == 12
    assert tex_module.round_half_up_fraction(Fraction(1, 8), 2, 'up') == 13
    assert tex_module.round_half_up_fraction(Fraction(3, 2), 1, 'round') == 15    # exact, no bump


# --- resolve_approx_params -------------------------------------------------

def test_resolve_approx_params_fills_round_defaults() -> None:
    params = tex_module.resolve_approx_params(kind='round')
    assert params.sig_digits == tex_module.APPROX_DEFAULT_SIG_DIGITS_ROUND
    assert (params.a_min, params.a_max) == (
        tex_module.APPROX_DEFAULT_ROUND_A_MIN, tex_module.APPROX_DEFAULT_ROUND_A_MAX
    )


def test_resolve_approx_params_estimate_needs_a_single_operator() -> None:
    with pytest.raises(ValueError, match="exactly one -o/--operator"):
        tex_module.resolve_approx_params(kind='estimate')
    with pytest.raises(ValueError, match="one of add, sub, mul, div"):
        tex_module.resolve_approx_params(kind='estimate', operator='mix')
    params = tex_module.resolve_approx_params(kind='estimate', operator='mul')
    assert params.operator == 'mul'
    assert params.sig_digits == tex_module.APPROX_DEFAULT_SIG_DIGITS_ESTIMATE


def test_resolve_approx_params_quotient_defaults_and_bounds() -> None:
    params = tex_module.resolve_approx_params(kind='quotient')
    assert params.quotient_decimal_places == tex_module.APPROX_DEFAULT_QUOTIENT_DECIMAL_PLACES
    assert params.dividend_decimal_places == tex_module.APPROX_DEFAULT_DIVIDEND_DECIMAL_PLACES
    with pytest.raises(ValueError, match="--quotient-decimal-places must be between 1 and"):
        tex_module.resolve_approx_params(kind='quotient', quotient_decimal_places=9)
    with pytest.raises(ValueError, match="--dividend-decimal-places must be between"):
        tex_module.resolve_approx_params(kind='quotient', dividend_decimal_places=5)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"kind": "round", "round_place": 2, "sig_digits": 2}, "cannot be combined"),
        ({"kind": "round", "round_place": 0}, "--round-place must be at least 1"),
        ({"kind": "quotient", "sig_digits": 2}, "not supported for approx --kind quotient"),
        ({"kind": "quotient", "round_method": "up"}, "always rounds the quotient by"),
        ({"kind": "round", "quotient_decimal_places": 2}, "only supported for approx --kind quotient"),
        ({"kind": "round", "a_min": 3, "a_max": 8, "sig_digits": 3}, "leaves every value"),
        ({"kind": "round", "a_min": 50, "a_max": 10}, "must not be inverted"),
    ],
)
def test_resolve_approx_params_rejects_invalid_combinations(kwargs, match) -> None:
    with pytest.raises(ValueError, match=match):
        tex_module.resolve_approx_params(**kwargs)


# --- generate_approx_problems -------------------------------------------

def _generate(kind: str, order: int = 12, **overrides):
    random.seed(20260903)
    params = tex_module.resolve_approx_params(kind=kind, **overrides)
    return tex_module.generate_approx_problems(
        params.kind, params.round_method, params.sig_digits, params.round_place,
        params.operator, params.quotient_decimal_places, params.dividend_decimal_places,
        list(range(params.a_min, params.a_max + 1)),
        list(range(params.b_min, params.b_max + 1)),
        order, 1,
    )


def test_generate_approx_round_problems_are_correctly_rounded() -> None:
    problems = _generate('round', order=25, sig_digits=2)
    assert [p.index for p in problems] == list(range(1, 26))
    for problem in problems:
        assert problem.kind == 'round'
        source = int(problem.expr_plain)
        assert int(problem.answer_plain) == tex_module._approx_round_value(source, 'round', 2, None)


def test_generate_approx_estimate_mul_rounds_then_multiplies() -> None:
    problems = _generate('estimate', order=25, operator='mul')
    for problem in problems:
        left, right = problem.expr_plain.split(' * ')
        rounded_a, rest = problem.answer_plain.split(' * ')
        rounded_b, result = rest.split(' = ')
        assert int(rounded_a) == tex_module._approx_round_value(int(left), 'round', 1, None)
        assert int(rounded_b) == tex_module._approx_round_value(int(right), 'round', 1, None)
        assert int(result) == int(rounded_a) * int(rounded_b)


def test_generate_approx_estimate_div_uses_evenly_dividing_rounded_operands() -> None:
    problems = _generate('estimate', order=20, operator='div')
    for problem in problems:
        rounded_a, rest = problem.answer_plain.split(' / ')
        rounded_b, result = rest.split(' = ')
        assert int(rounded_a) % int(rounded_b) == 0
        assert int(rounded_a) // int(rounded_b) == int(result)


def test_generate_approx_quotient_rounds_the_quotient_four_five() -> None:
    problems = _generate('quotient', order=25)
    for problem in problems:
        dividend_str, divisor_str = problem.expr_plain.split(' / ')
        dividend_scaled = int(dividend_str.replace('.', ''))
        expected = tex_module.round_half_up_fraction(
            Fraction(dividend_scaled, int(divisor_str) * 10), 2, 'round'
        )
        assert problem.answer_plain == tex_module.format_decimal_value(expected, 2)
        assert problem.answer_tex == problem.answer_plain  # quotient answer carries no operators


# --- renderers --------------------------------------------------------

def test_build_approx_block_tex_blank_hides_answer() -> None:
    problem = tex_module.ApproxProblem(
        index=1, kind='round', expr_tex='38472', answer_tex='38000',
        expr_plain='38472', answer_plain='38000',
    )
    blank_tex = tex_module.build_approx_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_approx_block_tex(problem, show_answer=True)
    assert '38000' not in blank_tex
    assert blank_tex == (
        '1) \\horizontaleq{38472 \\opspace \\fallingdotseq \\opspace \\hspace{1.5em}}'
    )
    assert filled_tex == (
        '1) \\horizontaleq{38472 \\opspace \\fallingdotseq \\opspace 38000}'
    )


def test_build_approx_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.ApproxProblem(
            index=1, kind='estimate', expr_tex='312 \\times 489',
            answer_tex='300 \\times 500 = 150000',
            expr_plain='312 * 489', answer_plain='300 * 500 = 150000',
        ),
        tex_module.ApproxProblem(
            index=2, kind='quotient', expr_tex='5.8 \\div 7', answer_tex='0.83',
            expr_plain='5.8 / 7', answer_plain='0.83',
        ),
    ]
    assert tex_module.build_approx_bottom_answer_tex(problems) == (
        '(1) $300 \\times 500 = 150000$ \\quad (2) $0.83$'
    )


def test_build_approx_csv_rows_has_one_row_per_problem() -> None:
    page1 = [
        tex_module.ApproxProblem(
            index=1, kind='round', expr_tex='38472', answer_tex='38000',
            expr_plain='38472', answer_plain='38000',
        ),
    ]
    rows = tex_module.build_approx_csv_rows([page1])
    assert rows == [[1, 1, 'round', '38472', '38000']]
