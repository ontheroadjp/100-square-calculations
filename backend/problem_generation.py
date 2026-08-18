"""
In-process problem-only generation: produce arithmetic problems as plain
Python data, without a subprocess call and without generating a PDF/LaTeX
document. This is the data-layer counterpart to renderers.py's
subprocess-based, PDF-generation (presentation) layer.

Only `command_type == 'ope'` (plain two-term arithmetic, the same shape
`nuts_calc.py`/`nuts_calc_tex.py` produce with no --use-parentheses/
--missing-value/--terms*/--mixed-operators flags) is supported today.
Every other command type -- and these `ope` variants -- raise ValueError;
see issue #166 and its sub-issues for the remaining command types.
"""

from typing import TypedDict

import nuts_calc
import nuts_calc_tex
import renderers

DEFAULT_A_MIN = 1
DEFAULT_A_MAX = 9
DEFAULT_B_MIN = 1
DEFAULT_B_MAX = 9
DEFAULT_OPERATOR = ["add"]

SYMBOL_TO_OPERATOR_NAME = {"+": "add", "-": "sub", "×": "mul", "÷": "div"}

UNSUPPORTED_OPE_VARIANT_FLAGS = (
    "use_parentheses",
    "missing_value",
    "terms",
    "terms_min",
    "terms_max",
    "mixed_operators",
)


class OpeProblemData(TypedDict, total=False):
    index: int
    a: int
    operator: str
    b: int
    result: int
    remainder: int
    a_decimal_places: int
    b_decimal_places: int
    intermediate_memo: str


def generate_problems(params: renderers.RendererRequest, renderer_name: str | None = None) -> list[OpeProblemData]:
    """
    Generate `params['num']` problems for `params['command_type']` using
    the active renderer's own data-generation functions, called directly
    in-process (no subprocess, no PDF/LaTeX byte output).
    """
    renderer_name = renderer_name or renderers.get_renderer_name()
    command_type = params.get("command_type")
    if command_type != "ope":
        raise ValueError(
            f"command_type {command_type!r} is not yet supported by problem-only "
            "generation; only 'ope' is supported today (see issue #166 and its sub-issues)."
        )
    for flag in UNSUPPORTED_OPE_VARIANT_FLAGS:
        if params.get(flag):
            raise ValueError(
                f"{flag!r} is not yet supported by problem-only generation for 'ope' "
                "(see issue #168)."
            )

    num = params.get("num")
    if not isinstance(num, int) or isinstance(num, bool) or num < 1:
        raise ValueError("num must be a positive integer")

    if renderer_name == "reportlab":
        return _generate_ope_problems_reportlab(params, num)
    return _generate_ope_problems_latex(params, num)


def _resolve_ope_range(
    params: renderers.RendererRequest, value_key: str, min_key: str, max_key: str,
    default_min: int, default_max: int,
) -> tuple[int, int]:
    digit_count = params.get(value_key)
    if digit_count is not None:
        return nuts_calc.set_min_max_value(digit_count)
    return params.get(min_key, default_min), params.get(max_key, default_max)


def _validate_intermediate(operator: list[str], b_max: int, single_digit_max: int) -> None:
    if operator != ["mul"]:
        raise ValueError("intermediate only supports a single 'mul' operator (operator=['mul']).")
    if b_max > single_digit_max:
        raise ValueError(f"intermediate only supports a single-digit second operand (b_max <= {single_digit_max}).")


def _generate_ope_problems_reportlab(params: renderers.RendererRequest, num: int) -> list[OpeProblemData]:
    a_min, a_max = _resolve_ope_range(params, "a_value", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = _resolve_ope_range(params, "b_value", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    intermediate = bool(params.get("intermediate", False))
    if intermediate:
        _validate_intermediate(operator, b_max, nuts_calc.SINGLE_DIGIT_MAX)

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    data = nuts_calc.get_operation_data(nums_a, nums_b, operator, order=num, print_index=1, intermediate=intermediate)
    if intermediate:
        data_index, vals_a, operator_mark, vals_b, _equal_marks, vals_aabb, _equal_marks2, vals_c = data
    else:
        data_index, vals_a, operator_mark, vals_b, _equal_marks, vals_c = data

    problems: list[OpeProblemData] = []
    for i in range(num):
        problem: OpeProblemData = {
            "index": int(data_index[i][0].rstrip(")")),
            "a": int(vals_a[i][0]),
            "operator": SYMBOL_TO_OPERATOR_NAME[operator_mark[i][0]],
            "b": int(vals_b[i][0]),
            "result": int(vals_c[i][0]),
            "remainder": 0,
            "a_decimal_places": 0,
            "b_decimal_places": 0,
        }
        if intermediate:
            problem["intermediate_memo"] = vals_aabb[i][0]
        problems.append(problem)
    return problems


def _generate_ope_problems_latex(params: renderers.RendererRequest, num: int) -> list[OpeProblemData]:
    a_min, a_max = _resolve_ope_range(params, "a_value", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = _resolve_ope_range(params, "b_value", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    intermediate = bool(params.get("intermediate", False))
    if intermediate:
        _validate_intermediate(operator, b_max, nuts_calc_tex.INTERMEDIATE_SINGLE_DIGIT_MAX)

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    a_decimal_places = params.get("a_decimal_places", nuts_calc_tex.MIN_DECIMAL_PLACES)
    b_decimal_places = params.get("b_decimal_places", nuts_calc_tex.MIN_DECIMAL_PLACES)
    ope_problems = nuts_calc_tex.generate_ope_problems(
        nums_a, nums_b, operator, num, 1,
        a_decimal_places, b_decimal_places,
        params.get("carry_mode"), params.get("remainder_mode"), params.get("result_max"),
    )

    problems: list[OpeProblemData] = []
    for ope_problem in ope_problems:
        problem: OpeProblemData = {
            "index": ope_problem.index,
            "a": ope_problem.a,
            "operator": ope_problem.operator,
            "b": ope_problem.b,
            "result": ope_problem.c,
            "remainder": ope_problem.remainder,
            "a_decimal_places": ope_problem.a_decimal_places,
            "b_decimal_places": ope_problem.b_decimal_places,
        }
        if intermediate:
            problem["intermediate_memo"] = nuts_calc_tex.build_intermediate_memo(ope_problem.a, ope_problem.b)
        problems.append(problem)
    return problems
