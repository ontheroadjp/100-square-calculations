"""
Pure-Python tests for `ope`'s decimal-arithmetic extension
(--a-decimal-places/--b-decimal-places).

Every test in this file exists to protect one invariant: a decimal result
must always be exact and finite (no floating point, no infinite/repeating
decimals anywhere) -- see nuts_calc_tex.py.md's decimal-arithmetic design
note.
"""

import random
from decimal import Decimal

import pytest

import nuts_calc_tex as tex_module


def test_format_decimal_value_zero_places_matches_plain_int_string() -> None:
    assert tex_module.format_decimal_value(5, 0) == "5"
    assert tex_module.format_decimal_value(123, 0) == "123"


def test_format_decimal_value_places_the_decimal_point() -> None:
    assert tex_module.format_decimal_value(5, 1) == "0.5"
    assert tex_module.format_decimal_value(360, 2) == "3.60"
    assert tex_module.format_decimal_value(9, 2) == "0.09"


@pytest.mark.parametrize(
    "operator, a_places, b_places, expected",
    [
        ("add", 2, 2, 2),
        ("sub", 1, 1, 1),
        ("mul", 1, 1, 2),
        ("mul", 2, 0, 2),
        ("div", 2, 0, 2),
        ("div", 1, 1, 0),
        # --integer-dividend: 0-place dividend / decimal divisor clamps to 0
        # (the quotient is a whole number by construction).
        ("div", 0, 1, 0),
    ],
)
def test_ope_result_decimal_places(operator: str, a_places: int, b_places: int, expected: int) -> None:
    assert tex_module.ope_result_decimal_places(operator, a_places, b_places) == expected


def test_generate_ope_problems_defaults_to_zero_decimal_places() -> None:
    problems = tex_module.generate_ope_problems([2], [3], ["add"], 5, 1)
    for problem in problems:
        assert problem.a_decimal_places == 0
        assert problem.b_decimal_places == 0


@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_generate_ope_problems_decimal_add_sub_mul_are_exact(operator: str) -> None:
    if operator in ("add", "sub"):
        nums_a, nums_b = list(range(10, 100)), list(range(10, 100))
        a_places = b_places = 2
    elif operator == "mul":
        nums_a, nums_b = list(range(10, 100)), list(range(1, 10))
        a_places, b_places = 1, 0
    else:
        nums_a, nums_b = list(range(10, 100)), list(range(1, 10))
        a_places, b_places = 1, 0

    problems = tex_module.generate_ope_problems(
        nums_a, nums_b, [operator], 50, 1, a_places, b_places,
    )
    assert len(problems) == 50
    for problem in problems:
        c_places = tex_module.ope_result_decimal_places(operator, a_places, b_places)
        a_value = Decimal(problem.a).scaleb(-a_places) if a_places else Decimal(problem.a)
        b_value = Decimal(problem.b).scaleb(-b_places) if b_places else Decimal(problem.b)
        c_value = Decimal(problem.c).scaleb(-c_places) if c_places else Decimal(problem.c)
        if operator == "add":
            assert a_value + b_value == c_value
        elif operator == "sub":
            assert a_value - b_value == c_value
            assert c_value > 0
        elif operator == "mul":
            assert a_value * b_value == c_value
        else:
            assert b_value != 0
            assert a_value / b_value == c_value


def test_generate_ope_problems_decimal_divide_by_decimal_yields_whole_number() -> None:
    nums_a = list(range(10, 100))
    nums_b = list(range(10, 100))
    problems = tex_module.generate_ope_problems(
        nums_a, nums_b, ["div"], 50, 1, a_decimal_places=1, b_decimal_places=1,
    )
    for problem in problems:
        c_places = tex_module.ope_result_decimal_places("div", 1, 1)
        assert c_places == 0
        # An exact integer quotient -- never a repeating/infinite decimal.
        assert problem.a % problem.b == 0
        assert problem.c == problem.a // problem.b


def test_generate_ope_problems_mixed_decimal_operand_order_mixes_both_orders() -> None:
    random.seed(1)
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(1, 10)), ["mul"], 60, 1,
        a_decimal_places=1, b_decimal_places=0,
        mixed_decimal_operand_order=True,
    )
    assert len(problems) == 60
    seen_orders = {(problem.a_decimal_places, problem.b_decimal_places) for problem in problems}
    # Both "decimal x integer" (1, 0) and "integer x decimal" (0, 1) appear.
    assert seen_orders == {(1, 0), (0, 1)}
    for problem in problems:
        assert {problem.a_decimal_places, problem.b_decimal_places} == {0, 1}
        c_places = tex_module.ope_result_decimal_places(
            "mul", problem.a_decimal_places, problem.b_decimal_places,
        )
        assert c_places == 1
        a_value = (
            Decimal(problem.a).scaleb(-problem.a_decimal_places)
            if problem.a_decimal_places else Decimal(problem.a)
        )
        b_value = (
            Decimal(problem.b).scaleb(-problem.b_decimal_places)
            if problem.b_decimal_places else Decimal(problem.b)
        )
        c_value = Decimal(problem.c).scaleb(-c_places)
        assert a_value * b_value == c_value


def test_generate_ope_problems_integer_dividend_yields_whole_dividend_and_quotient() -> None:
    # grade-5 "整数と小数の割り算" 整数÷小数 option (issue #317): the frontend
    # sends a_decimal_places=0 for the dividend and b_decimal_places=1 for the
    # decimal divisor.
    random.seed(7)
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(10, 100)), ["div"], 50, 1,
        a_decimal_places=0, b_decimal_places=1, dividend_mode="integer",
    )
    assert len(problems) == 50
    for problem in problems:
        assert problem.a_decimal_places == 0            # dividend shown as a whole number
        assert problem.b_decimal_places == 1            # divisor is a decimal
        assert problem.b % 10 != 0                      # ...and a genuine one (not b.0)
        assert problem.remainder == 0
        c_places = tex_module.ope_result_decimal_places("div", 0, 1)
        assert c_places == 0
        dividend = Decimal(problem.a)
        divisor = Decimal(problem.b).scaleb(-1)
        assert dividend / divisor == Decimal(problem.c)  # exact whole-number quotient


def test_generate_ope_problems_mixed_dividend_mixes_whole_and_decimal_dividends() -> None:
    random.seed(3)
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(10, 100)), ["div"], 60, 1,
        a_decimal_places=1, b_decimal_places=1, dividend_mode="mixed",
    )
    assert len(problems) == 60
    seen_dividend_places = {problem.a_decimal_places for problem in problems}
    assert seen_dividend_places == {0, 1}               # both whole and decimal dividends appear
    for problem in problems:
        assert problem.b_decimal_places == 1
        c_places = tex_module.ope_result_decimal_places("div", problem.a_decimal_places, 1)
        dividend = (
            Decimal(problem.a).scaleb(-problem.a_decimal_places)
            if problem.a_decimal_places else Decimal(problem.a)
        )
        divisor = Decimal(problem.b).scaleb(-1)
        quotient = Decimal(problem.c).scaleb(-c_places) if c_places else Decimal(problem.c)
        assert dividend / divisor == quotient


def test_generate_ope_problems_decimal_dividend_mode_matches_the_default() -> None:
    kwargs = dict(a_decimal_places=1, b_decimal_places=1)
    random.seed(11)
    without_flag = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(10, 100)), ["div"], 40, 1, **kwargs,
    )
    random.seed(11)
    with_decimal = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(10, 100)), ["div"], 40, 1,
        dividend_mode="decimal", **kwargs,
    )
    assert [ (p.a, p.b, p.c) for p in without_flag ] == [ (p.a, p.b, p.c) for p in with_decimal ]


def test_generate_ope_problems_without_mixed_flag_keeps_fixed_operand_order() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(1, 10)), ["mul"], 30, 1,
        a_decimal_places=1, b_decimal_places=0,
    )
    for problem in problems:
        assert problem.a_decimal_places == 1
        assert problem.b_decimal_places == 0


def test_build_horizontal_block_tex_renders_decimal_points() -> None:
    problem = tex_module.OpeProblem(
        index=1, a=360, b=280, operator="add", c=640,
        a_decimal_places=2, b_decimal_places=2,
    )
    filled = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    blank = tex_module.build_horizontal_block_tex(problem, show_answer=False)
    assert (
        "3.60 \\opspace + \\opspace 2.80 \\opspace = \\opspace 6.40" in filled
    )
    assert "3.60 \\opspace + \\opspace 2.80" in blank
    assert "6.40" not in blank


def test_build_ope_bottom_answer_tex_formats_decimal_result() -> None:
    problem = tex_module.OpeProblem(
        index=1, a=50, b=8, operator="mul", c=400,
        a_decimal_places=1, b_decimal_places=0,
    )
    assert tex_module.build_ope_bottom_answer_tex([problem]) == "(1) 40.0"


def test_build_ope_csv_rows_keeps_plain_ints_when_no_decimal_places() -> None:
    problem = tex_module.OpeProblem(index=1, a=2, b=3, operator="add", c=5)
    assert tex_module.build_ope_csv_rows([[problem]]) == [[1, 1, 2, "add", 3, 5, 0]]


def test_build_ope_csv_rows_formats_decimal_values() -> None:
    problem = tex_module.OpeProblem(
        index=1, a=50, b=8, operator="mul", c=400,
        a_decimal_places=1, b_decimal_places=0,
    )
    assert tex_module.build_ope_csv_rows([[problem]]) == [[1, 1, "5.0", "mul", "8", "40.0", 0]]


def _decimal_remainder_problem() -> "tex_module.OpeProblem":
    # 7.6 / 3 = 2 ... 1.6 (issue #333): whole-number quotient, decimal remainder.
    return tex_module.OpeProblem(
        index=1, a=76, b=3, operator="div", c=2,
        a_decimal_places=1, b_decimal_places=0,
        remainder=16, remainder_decimal_places=1, result_decimal_places=0,
    )


def test_build_ope_slot_content_tex_renders_decimal_remainder_tail() -> None:
    problem = _decimal_remainder_problem()
    filled = tex_module.build_ope_slot_content_tex(problem, show_answer=True)
    blank = tex_module.build_ope_slot_content_tex(problem, show_answer=False)
    assert filled == (
        "\\horizontaleq{7.6 \\opspace \\div \\opspace 3 \\opspace = \\opspace 2 \\cdots 1.6}"
    )
    # quotient prints as a whole number "2", not "0.2"
    assert "0.2" not in filled
    assert "1.6" not in blank and " \\cdots " in blank


def test_build_ope_bottom_answer_tex_renders_decimal_remainder() -> None:
    assert tex_module.build_ope_bottom_answer_tex([_decimal_remainder_problem()]) == "(1) 2 ... 1.6"


def test_build_ope_csv_rows_formats_decimal_remainder() -> None:
    assert tex_module.build_ope_csv_rows([[_decimal_remainder_problem()]]) == [
        [1, 1, "7.6", "div", "3", "2", "1.6"],
    ]


def test_ope_problem_result_decimal_places_defaults_match_ope_result_decimal_places() -> None:
    # No override -> byte-identical to the pre-#333 derivation for every operator.
    for operator, a_dp, b_dp in [("add", 2, 2), ("mul", 1, 1), ("div", 1, 0), ("div", 2, 1)]:
        problem = tex_module.OpeProblem(
            index=1, a=1, b=1, operator=operator, c=1,
            a_decimal_places=a_dp, b_decimal_places=b_dp,
        )
        assert tex_module.ope_problem_result_decimal_places(problem) == (
            tex_module.ope_result_decimal_places(operator, a_dp, b_dp)
        )
    # Explicit override wins.
    assert tex_module.ope_problem_result_decimal_places(_decimal_remainder_problem()) == 0
