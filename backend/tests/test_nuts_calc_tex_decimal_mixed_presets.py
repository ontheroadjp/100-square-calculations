"""
Regression coverage for the decimal (`ope --a-decimal-places`/
`--b-decimal-places`) and "mixed" (int/decimal/fraction) preset design used
by `web/frontend/src/drillPresets.js` (issue #76).

`generate_mixed_problems` has no deterministic fallback (like
`generate_multi_term_ope_problems`/`generate_tree_ope_problems`, see
docs/L3_implementation/nuts_calc_tex.py.md) and can raise ValueError for
kind/digit/term-count combinations with too few valid solutions. This file
exercises the exact parameter combinations the 7 new preset cards use
directly against nuts_calc_tex.py's generation functions (no pdflatex
required) to confirm they don't exhaust MAX_OPERAND_RETRY_ATTEMPTS in
practice, and that every generated decimal/division result stays exact (no
infinite/repeating decimals -- see the same doc's decimal-arithmetic design
note).

Keep the configurations below in sync with `drillPresets.js`'s
g3/g4/g5-decimal-* and g6-mixed-* preset params.
"""

import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

TRIALS_PER_CONFIG = 20
PROBLEMS_PER_TRIAL = 15


def _digit_range(value: int) -> tuple[int, int]:
    digits_list = ((1, 9), (10, 99), (100, 999))
    return digits_list[value - 1]


# Mirrors drillPresets.js's g{grade}-decimal-* preset params.
DECIMAL_OPE_PRESETS = [
    pytest.param("g3-decimal-addsub", ["add", "sub"], 1, 1, 1, 1, id="g3-decimal-addsub"),
    pytest.param("g4-decimal-addsub", ["add", "sub"], 3, 3, 2, 2, id="g4-decimal-addsub"),
    pytest.param("g4-decimal-mul", ["mul"], 2, 1, 1, 0, id="g4-decimal-mul"),
    pytest.param("g4-decimal-div", ["div"], 2, 1, 1, 0, id="g4-decimal-div"),
    pytest.param("g5-decimal-mul", ["mul"], 2, 2, 1, 1, id="g5-decimal-mul"),
    pytest.param("g5-decimal-div", ["div"], 2, 2, 1, 1, id="g5-decimal-div"),
]


@pytest.mark.parametrize("preset_id,operators,a_value,b_value,a_dp,b_dp", DECIMAL_OPE_PRESETS)
def test_decimal_ope_preset_config_generates_exact_results(
    preset_id: str, operators: list[str], a_value: int, b_value: int, a_dp: int, b_dp: int,
) -> None:
    a_min, a_max = _digit_range(a_value)
    b_min, b_max = _digit_range(b_value)
    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))

    for _ in range(TRIALS_PER_CONFIG):
        problems = tex_module.generate_ope_problems(
            nums_a, nums_b, operators, PROBLEMS_PER_TRIAL, 1, a_dp, b_dp,
        )
        assert len(problems) == PROBLEMS_PER_TRIAL
        for problem in problems:
            c_places = tex_module.ope_result_decimal_places(problem.operator, a_dp, b_dp)
            a_decimal = Decimal(problem.a).scaleb(-a_dp) if a_dp else Decimal(problem.a)
            b_decimal = Decimal(problem.b).scaleb(-b_dp) if b_dp else Decimal(problem.b)
            c_decimal = Decimal(problem.c).scaleb(-c_places) if c_places else Decimal(problem.c)
            if problem.operator == "add":
                assert a_decimal + b_decimal == c_decimal
            elif problem.operator == "sub":
                assert a_decimal - b_decimal == c_decimal
                assert c_decimal > 0
            elif problem.operator == "mul":
                assert a_decimal * b_decimal == c_decimal
            else:
                assert a_decimal / b_decimal == c_decimal


# Mirrors drillPresets.js's g6-mixed-basic/g6-mixed-advanced preset params.
MIXED_PRESETS = [
    pytest.param("g6-mixed-basic", 2, 2, False, id="g6-mixed-basic"),
    pytest.param("g6-mixed-advanced", 3, 3, True, id="g6-mixed-advanced"),
]


@pytest.mark.parametrize("preset_id,terms_min,terms_max,mixed_operators", MIXED_PRESETS)
def test_mixed_preset_config_generates_exact_fraction_results(
    preset_id: str, terms_min: int, terms_max: int, mixed_operators: bool,
) -> None:
    kinds = ["int", "decimal", "fraction"]

    for _ in range(TRIALS_PER_CONFIG):
        problems = tex_module.generate_mixed_problems(
            kinds, kinds, ["mix"], mixed_operators, 1, 1, 1,
            terms_min, terms_max, PROBLEMS_PER_TRIAL, 1,
        )
        assert len(problems) == PROBLEMS_PER_TRIAL
        for problem in problems:
            assert terms_min <= len(problem.operands) <= terms_max
            assert isinstance(problem.result, Fraction)
            assert problem.result > 0
            values = [operand.value for operand in problem.operands]
            expected = (
                tex_module.evaluate_mixed_expression(values, problem.operators, tex_module.MIXED_STAGE_FUNCTIONS)
                if mixed_operators
                else tex_module.evaluate_left_to_right(values, problem.operators, tex_module.MIXED_STAGE_FUNCTIONS)
            )
            assert problem.result == expected
