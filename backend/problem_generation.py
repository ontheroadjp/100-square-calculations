"""
In-process problem-only generation: produce arithmetic problems as plain
Python data, without a subprocess call and without generating a PDF/LaTeX
document. This is the data-layer counterpart to renderers.py's
subprocess-based, PDF-generation (presentation) layer.

`command_type == 'ope'` is supported, including its --use-parentheses/
--missing-value/--terms*/--mixed-operators variants (issue #168). Every
other command type raises ValueError; see issue #166 and its sub-issues
for the remaining command types.
"""

import dataclasses
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


def generate_problems(params: renderers.RendererRequest, renderer_name: str | None = None) -> list[dict[str, object]]:
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

    num = params.get("num")
    if not isinstance(num, int) or isinstance(num, bool) or num < 1:
        raise ValueError("num must be a positive integer")

    variant, terms_min, terms_max = _determine_ope_variant(params)
    if variant is not None:
        if renderer_name == "reportlab":
            raise ValueError(
                f"ope's {variant!r} variant is not supported by the reportlab renderer "
                "(nuts_calc.py has no --use-parentheses/--missing-value/--terms equivalent)."
            )
        if variant == "tree":
            return _generate_tree_ope_problems(params, num, terms_min, terms_max)
        if variant == "missing_value":
            return _generate_missing_value_problems(params, num)
        return _generate_multi_term_ope_problems(params, num, terms_min, terms_max)

    if renderer_name == "reportlab":
        return _generate_ope_problems_reportlab(params, num)
    return _generate_ope_problems_latex(params, num)


def _determine_ope_variant(params: renderers.RendererRequest) -> tuple[str | None, int, int]:
    """
    Decide which `ope` problem shape `params` requests -- 'tree'
    (--use-parentheses), 'missing_value' (--missing-value), 'multi_term'
    (--terms/--terms-min/--terms-max/--mixed-operators), or None (plain
    2-term) -- and resolve/validate the term-count range the same way
    nuts_calc_tex.py's _init() does (nuts_calc_tex.py:606-645,712-715),
    since this endpoint bypasses argparse and its defaults/validation.
    """
    use_parentheses = bool(params.get("use_parentheses", False))
    missing_value = bool(params.get("missing_value", False))
    mixed_operators = bool(params.get("mixed_operators", False))
    terms = params.get("terms")
    terms_min = params.get("terms_min", nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    terms_max = params.get("terms_max", nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    if terms is not None:
        terms_min = terms_max = terms

    terms_options_given = (
        terms is not None
        or terms_min != nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT
        or terms_max != nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT
        or mixed_operators
    )

    if missing_value and use_parentheses:
        raise ValueError("missing_value cannot be combined with use_parentheses.")
    if missing_value and terms_options_given:
        raise ValueError(
            "missing_value cannot be combined with the terms family "
            "(terms/terms_min/terms_max/mixed_operators)."
        )
    if terms_options_given and terms_min > terms_max:
        raise ValueError("terms_min must be less than or equal to terms_max.")

    if use_parentheses or terms_options_given:
        terms_min, terms_max = nuts_calc_tex.resolve_term_range(terms_min, terms_max, use_parentheses)

    if use_parentheses:
        return "tree", terms_min, terms_max
    if missing_value:
        return "missing_value", terms_min, terms_max
    if terms_options_given:
        return "multi_term", terms_min, terms_max
    return None, terms_min, terms_max


def _dataclass_to_dict(value: object) -> object:
    """
    Recursively convert a dataclass instance (and any nested dataclasses/
    lists) into plain JSON-serializable dicts/lists, using field names
    as-is -- the JSON contract decided in issue #167 for non-2-term `ope`
    problem shapes (docs/L3_implementation/backend/problem_generation.py.md).
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _dataclass_to_dict(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, list):
        return [_dataclass_to_dict(item) for item in value]
    return value


def _generate_tree_ope_problems(
    params: renderers.RendererRequest, num: int, terms_min: int, terms_max: int,
) -> list[dict[str, object]]:
    a_min, a_max = _resolve_ope_range(params, "a_value", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = _resolve_ope_range(params, "b_value", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    mixed_operators = bool(params.get("mixed_operators", False))

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_tree_ope_problems(
        nums_a, nums_b, operator, mixed_operators, terms_min, terms_max, num, 1, params.get("result_max"),
    )
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_multi_term_ope_problems(
    params: renderers.RendererRequest, num: int, terms_min: int, terms_max: int,
) -> list[dict[str, object]]:
    a_min, a_max = _resolve_ope_range(params, "a_value", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = _resolve_ope_range(params, "b_value", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    mixed_operators = bool(params.get("mixed_operators", False))

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_multi_term_ope_problems(
        nums_a, nums_b, operator, mixed_operators, terms_min, terms_max, num, 1, params.get("result_max"),
    )
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_missing_value_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min, a_max = _resolve_ope_range(params, "a_value", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = _resolve_ope_range(params, "b_value", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_missing_value_problems(
        nums_a, nums_b, operator, num, 1, params.get("result_max"),
    )
    return [_dataclass_to_dict(problem) for problem in problems]


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
