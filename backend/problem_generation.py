"""
In-process problem-only generation: produce arithmetic problems as plain
Python data, without a subprocess call and without generating a PDF/LaTeX
document. This is the data-layer counterpart to renderers.py's
subprocess-based, PDF-generation (presentation) layer.

`command_type == 'ope'` is supported, including its --use-parentheses/
--missing-value/--terms*/--mixed-operators variants (issue #168), as are
`com`/`99`/`aBc`/`squ`/`pi` (issue #169), `frac`/`mixed` (issue #170),
`compare` (issue #171), `evenodd`/`multiples`/`divisors`/`lcm`/`gcd`
(issue #172), and `simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac`
(issue #173) via `_COMMAND_GENERATORS`. `100` is also supported, but NOT
through `_COMMAND_GENERATORS` or the `{"problems": [...]}` envelope: its
nuts_calc_tex.py `generate_hundred_square()` output is a single 10x10
HundredSquareTable, not a `num`-many problem list, so
`generate_hundred_square_table()` returns it in a dedicated top-level
`{"table": {...}}` envelope instead (a sibling key to `problems`, never
nested inside it). This reverses issue #169's earlier decision to exclude
`100` here, per the 2026-08-19 /mtg on issue #174 (issue #228). Every other
command type raises ValueError; see issue #166.
"""

import dataclasses
import math
from fractions import Fraction
from typing import Callable, TypedDict

import nuts_calc_tex
import renderers

DEFAULT_A_MIN = 1
DEFAULT_A_MAX = 9
DEFAULT_B_MIN = 1
DEFAULT_B_MAX = 9
DEFAULT_OPERATOR = ["add"]


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
    nuts_calc_tex.py's data-generation functions, called directly in-process
    (no subprocess, no PDF/LaTeX byte output).

    `renderer_name` is resolved via `renderers.get_renderer_name()` when not
    given, purely to fail fast with a clear error for any renderer other
    than `latex` (issue #232 removed nuts_calc.py/reportlab, the only other
    renderer this endpoint ever supported) -- the resolved value itself is
    not otherwise used, since every supported command_type now has exactly
    one implementation. The parameter is kept as the extension point for a
    future second renderer, should one be added.
    """
    renderer_name = renderer_name or renderers.get_renderer_name()
    command_type = params.get("command_type")

    num = params.get("num")
    if not isinstance(num, int) or isinstance(num, bool) or num < 1:
        raise ValueError("num must be a positive integer")

    if command_type == "ope":
        return _generate_ope_problems(params, num)

    if command_type == "100":
        # `100` is served through generate_hundred_square_table()'s dedicated
        # `{"table": {...}}` envelope, not this function's `{"problems": [...]}`
        # list contract (issue #228). The `/generate-problems` endpoint routes
        # `100` there before ever calling generate_problems(); this branch only
        # guards direct callers, giving them an explicit pointer instead of the
        # generic "not yet supported" fallthrough below -- which would now be
        # misleading, since `100` IS supported, just with a different shape.
        raise ValueError(
            "command_type '100' is served by generate_hundred_square_table(), not "
            "generate_problems(); its single 10x10 table does not fit the "
            '\'{"problems": [...]}\' list contract (issue #228).'
        )

    generator = _COMMAND_GENERATORS.get(command_type)
    if generator is None:
        raise ValueError(
            f"command_type {command_type!r} is not yet supported by problem-only "
            "generation; see issue #166 and its sub-issues for supported command types."
        )
    return generator(params, num)


def _generate_ope_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    variant, terms_min, terms_max = _determine_ope_variant(params)
    if variant is not None:
        if variant == "tree":
            return _generate_tree_ope_problems(params, num, terms_min, terms_max)
        if variant == "missing_value":
            return _generate_missing_value_problems(params, num)
        return _generate_multi_term_ope_problems(params, num, terms_min, terms_max)

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
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    return value


def _generate_tree_ope_problems(
    params: renderers.RendererRequest, num: int, terms_min: int, terms_max: int,
) -> list[dict[str, object]]:
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
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
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    mixed_operators = bool(params.get("mixed_operators", False))

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_multi_term_ope_problems(
        nums_a, nums_b, operator, mixed_operators, terms_min, terms_max, num, 1, params.get("result_max"),
    )
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_missing_value_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_missing_value_problems(
        nums_a, nums_b, operator, num, 1, params.get("result_max"),
    )
    return [_dataclass_to_dict(problem) for problem in problems]


def resolve_digit_count_range(
    params: renderers.RendererRequest, digits_key: str, min_key: str, max_key: str,
    default_min: int, default_max: int,
) -> tuple[int, int]:
    """
    Single shared resolver (issue #230) for the a/b range of any command in
    nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS (ope/100/lcm/gcd/divfrac):
    `digits_key` ("a_digits"/"b_digits") is the digit-count shorthand,
    converted via nuts_calc_tex.set_min_max_value(); if absent, falls back to
    the explicit `min_key`/`max_key` range. Every future _generate_*_pdf-style
    builder for this command family must call this instead of reimplementing
    the conversion, to keep it centralized at one call site per command.
    """
    digit_count = params.get(digits_key)
    if digit_count is not None:
        return nuts_calc_tex.set_min_max_value(digit_count)
    return params.get(min_key, default_min), params.get(max_key, default_max)


# Minimum distinct values each `100` axis range must span. nuts_calc_tex's
# sample_hundred_square_values() duplicates the axis list
# HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR times, then draws HUNDRED_SQUARE_SIZE
# without replacement, so a shorter range makes its bare `random.sample`
# raise an unexplained ValueError; generate_hundred_square_table() checks
# this threshold first to raise an explanatory one instead.
_HUNDRED_SQUARE_MIN_AXIS_VALUES = (
    nuts_calc_tex.HUNDRED_SQUARE_SIZE // nuts_calc_tex.HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR
)


def generate_hundred_square_table(params: renderers.RendererRequest) -> dict[str, object]:
    """Generate one `100` addition table for the `/generate-problems` endpoint.

    `100` is the single command_type this endpoint serves that does NOT use
    the `{"problems": [...]}` envelope every other command shares. A single
    10x10 addition table has no natural `num`-many "problem" decomposition,
    so the `problems` list would force an artificial shape onto it. Instead
    this returns a dedicated top-level `table` key -- a sibling of `problems`,
    never nested inside it::

        {"table": {"left_values": [ ...10 ints... ],
                   "top_values":  [ ...10 ints... ],
                   "answers":     [ [ ...10 ints... ], ...10 rows total... ]}}

    where ``answers[r][c] == left_values[r] + top_values[c]``. This reverses
    issue #169's decision to exclude `100` from `/generate-problems`, per the
    2026-08-19 /mtg on issue #174 (issue #228).

    The a/b ranges are resolved exactly like the other
    nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS via
    `resolve_digit_count_range` (a_digits/b_digits digit-count shorthand,
    else explicit a_min/a_max / b_min/b_max, else the module DEFAULT_*_MIN/MAX
    of 1..9). `params` may carry `num` -- the endpoint keeps it required for
    uniform input validation across all command types -- but it is
    semantically irrelevant here and is ignored, mirroring how the CLI
    accepts but ignores rows/columns/with_bottom_answer for `100`.

    Raises ValueError if either axis range spans fewer than
    `_HUNDRED_SQUARE_MIN_AXIS_VALUES` distinct values (see that constant).
    """
    a_min, a_max = resolve_digit_count_range(
        params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX,
    )
    b_min, b_max = resolve_digit_count_range(
        params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX,
    )
    nums_left = list(range(a_min, a_max + 1))
    nums_top = list(range(b_min, b_max + 1))
    if (
        len(nums_left) < _HUNDRED_SQUARE_MIN_AXIS_VALUES
        or len(nums_top) < _HUNDRED_SQUARE_MIN_AXIS_VALUES
    ):
        raise ValueError(
            f"the '100' command needs an a/b range of at least "
            f"{_HUNDRED_SQUARE_MIN_AXIS_VALUES} distinct values to fill the "
            f"{nuts_calc_tex.HUNDRED_SQUARE_SIZE}x{nuts_calc_tex.HUNDRED_SQUARE_SIZE} table"
        )

    table = nuts_calc_tex.generate_hundred_square(nums_left, nums_top)
    return {
        "table": {
            "left_values": table.left_values,
            "top_values": table.top_values,
            "answers": table.answers,
        }
    }


def _validate_intermediate(operator: list[str], b_max: int, single_digit_max: int) -> None:
    if operator != ["mul"]:
        raise ValueError("intermediate only supports a single 'mul' operator (operator=['mul']).")
    if b_max > single_digit_max:
        raise ValueError(f"intermediate only supports a single-digit second operand (b_max <= {single_digit_max}).")


def _generate_ope_problems_latex(params: renderers.RendererRequest, num: int) -> list[OpeProblemData]:
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
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


def validate_com_target(a_value: int | None) -> int:
    """Validate the 'com' command's complement target (issue #237).

    Shared by `_generate_com_problems` (below) and `backend/app.py`'s
    `_generate_com_pdf`, which independently duplicated this check before
    issue #237.
    """
    if a_value is None:
        raise ValueError("a_value (complement target) is required for the 'com' command.")
    if a_value < nuts_calc_tex.MIN_COMPLEMENT_TARGET:
        raise ValueError(
            f"a_value (complement target) must be at least {nuts_calc_tex.MIN_COMPLEMENT_TARGET} "
            "for the 'com' command."
        )
    return a_value


def _generate_com_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    target = validate_com_target(params.get("a_value"))
    problems = nuts_calc_tex.generate_com_problems(target, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def validate_kuku_a_value(a_value: int | None) -> int:
    """Validate the '99' command's times-table row value (issue #208).

    Shared by `_generate_kuku_problems` (below) and `backend/app.py`'s
    `_generate_kuku_pdf`, following `validate_com_target`'s dedupe pattern
    (issue #237).
    """
    if a_value is None:
        raise ValueError("a_value (times-table row) is required for the '99' command.")
    return a_value


def _generate_kuku_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_value = validate_kuku_a_value(params.get("a_value"))
    descend = bool(params.get("descend", False))
    shuffle = bool(params.get("shuffle", False))
    problems = nuts_calc_tex.generate_kuku_problems(a_value, num, 1, descend, shuffle)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_abc_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    problems = nuts_calc_tex.generate_abc_problems(num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def validate_squ_start(a_value: int | None) -> int:
    """Validate the 'squ' command's starting square number (issue #209).

    Shared by `_generate_squ_problems` (below) and `backend/app.py`'s
    `_generate_squ_pdf`, following the dedupe pattern `validate_com_target`
    established for 'com' (issue #237).
    """
    if a_value is None:
        raise ValueError("a_value (starting square number) is required for the 'squ' command.")
    return a_value


def _generate_squ_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    start_num = validate_squ_start(params.get("a_value"))
    descend = bool(params.get("descend", False))
    shuffle = bool(params.get("shuffle", False))
    problems = nuts_calc_tex.generate_squ_problems(start_num, num, 1, descend, shuffle)
    return [_dataclass_to_dict(problem) for problem in problems]


def validate_pi_start(a_value: int | None) -> int:
    """Validate the 'pi' command's starting multiplicand (issue #210).

    Shared by `_generate_pi_problems` (below) and `backend/app.py`'s
    `_generate_pi_pdf`, following the `validate_com_target` pattern
    (issue #237) instead of duplicating this check in both places.
    """
    if a_value is None:
        raise ValueError("a_value (starting multiplicand) is required for the 'pi' command.")
    return a_value


def _generate_pi_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    start_num = validate_pi_start(params.get("a_value"))
    descend = bool(params.get("descend", False))
    shuffle = bool(params.get("shuffle", False))
    problems = nuts_calc_tex.generate_pi_problems(start_num, num, 1, descend, shuffle)
    return [_dataclass_to_dict(problem) for problem in problems]


def _validate_fraction_digits(numerator_digits: int, denominator_digits: int, command_type: str) -> None:
    for option_name, value in (
        ("numerator_digits", numerator_digits), ("denominator_digits", denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the {command_type!r} command."
            )


def _validate_reducible_operators(operator: list[str], command_type: str) -> None:
    allowed_reducible_operators = {"mul", "div"}
    if not operator or not set(operator) <= allowed_reducible_operators:
        raise ValueError(
            f"reducible_mode only supports 'mul'/'div' operators for the {command_type!r} command."
        )


def _generate_frac_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "frac")

    same_denominator = bool(params.get("same_denominator", False))
    different_denominators = bool(params.get("different_denominators", False))
    if same_denominator and different_denominators:
        raise ValueError("same_denominator and different_denominators cannot be combined.")

    proper_operands = bool(params.get("proper_operands", False))
    if proper_operands and numerator_digits > denominator_digits:
        raise ValueError(
            "proper_operands requires numerator_digits to be no greater than denominator_digits."
        )
    proper_result = bool(params.get("proper_result", False))

    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    a_fraction_form = params.get("a_fraction_form", "proper")
    b_fraction_form = params.get("b_fraction_form", "proper")
    if a_fraction_form != "proper" or b_fraction_form != "proper":
        if operator not in (["add"], ["sub"]):
            raise ValueError(
                "a_fraction_form/b_fraction_form require operator=['add'] or "
                "operator=['sub'] for the 'frac' command."
            )
        if "improper" in (a_fraction_form, b_fraction_form):
            raise ValueError("a_fraction_form/b_fraction_form do not support 'improper' for the 'frac' command.")

    reducible_mode = params.get("reducible_mode")
    if reducible_mode is not None:
        _validate_reducible_operators(operator, "frac")

    problems = nuts_calc_tex.generate_fraction_problems(
        numerator_digits, denominator_digits, operator, num, 1, same_denominator,
        proper_operands, proper_result, different_denominators,
        a_fraction_form, b_fraction_form, reducible_mode,
    )
    return [_dataclass_to_dict(problem) for problem in problems]


def _determine_mixed_terms(params: renderers.RendererRequest, mixed_operators: bool) -> tuple[int, int, bool]:
    """Resolve/validate the 'mixed' command's terms_min/terms_max the same
    way nuts_calc_tex.py's _init() does (nuts_calc_tex.py:624-635,709-715),
    since this endpoint bypasses argparse and its defaults/validation.
    """
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
    if terms_options_given and terms_min > terms_max:
        raise ValueError("terms_min must be less than or equal to terms_max.")

    terms_min, terms_max = nuts_calc_tex.resolve_term_range(terms_min, terms_max, False)
    return terms_min, terms_max, terms_options_given


def _generate_mixed_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "mixed")

    decimal_places = params.get("decimal_places", 1)
    if not nuts_calc_tex.MIN_DECIMAL_PLACES <= decimal_places <= nuts_calc_tex.MAX_DECIMAL_PLACES:
        raise ValueError(
            f"decimal_places must be between {nuts_calc_tex.MIN_DECIMAL_PLACES} and "
            f"{nuts_calc_tex.MAX_DECIMAL_PLACES} for the 'mixed' command."
        )

    a_kind = list(params.get("a_kind") or nuts_calc_tex.MIXED_OPERAND_KINDS)
    b_kind = list(params.get("b_kind") or nuts_calc_tex.MIXED_OPERAND_KINDS)
    operator = list(params.get("operator") or DEFAULT_OPERATOR)
    mixed_operators = bool(params.get("mixed_operators", False))

    terms_min, terms_max, terms_options_given = _determine_mixed_terms(params, mixed_operators)

    reducible_mode = params.get("reducible_mode")
    if reducible_mode is not None:
        _validate_reducible_operators(operator, "mixed")
        if terms_options_given:
            raise ValueError(
                "reducible_mode cannot be combined with terms/terms_min/terms_max/mixed_operators "
                "for the 'mixed' command."
            )
        if {tuple(a_kind), tuple(b_kind)} != {("fraction",), ("int",)}:
            raise ValueError(
                "reducible_mode requires exactly one a_kind=['fraction']/b_kind=['int'] pairing "
                "(in either order) for the 'mixed' command."
            )

    problems = nuts_calc_tex.generate_mixed_problems(
        a_kind, b_kind, operator, mixed_operators,
        numerator_digits, denominator_digits, decimal_places,
        terms_min, terms_max, num, 1, reducible_mode,
    )
    return [_dataclass_to_dict(problem) for problem in problems]


DEFAULT_COMPARISON_KIND = ["fraction"]


def _generate_compare_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "compare")

    decimal_places = params.get("decimal_places", 1)
    if not nuts_calc_tex.MIN_DECIMAL_PLACES <= decimal_places <= nuts_calc_tex.MAX_DECIMAL_PLACES:
        raise ValueError(
            f"decimal_places must be between {nuts_calc_tex.MIN_DECIMAL_PLACES} and "
            f"{nuts_calc_tex.MAX_DECIMAL_PLACES} for the 'compare' command."
        )

    a_kind = list(params.get("a_kind") or DEFAULT_COMPARISON_KIND)
    b_kind = list(params.get("b_kind") or DEFAULT_COMPARISON_KIND)

    pattern = params.get("comparison_pattern", "different-denominators")
    if pattern != "different-denominators" and (a_kind != DEFAULT_COMPARISON_KIND or b_kind != DEFAULT_COMPARISON_KIND):
        # Mirrors nuts_calc_tex.py's _init(): same-denominator/same-numerator/
        # different-denominators only have meaning when both sides are
        # fractions (int operands always have denominator 1, decimal operands
        # always have denominator 10**decimal_places).
        raise ValueError(
            "comparison_pattern requires a_kind=['fraction'] and b_kind=['fraction'] "
            "for the 'compare' command."
        )

    a_fraction_form = params.get("a_fraction_form", "proper")
    b_fraction_form = params.get("b_fraction_form", "proper")

    problems = nuts_calc_tex.generate_fraction_comparison_problems(
        pattern, a_fraction_form, b_fraction_form, numerator_digits, denominator_digits, num, 1,
        a_kind, b_kind, decimal_places,
    )
    result = []
    for problem in problems:
        item = _dataclass_to_dict(problem)
        item["relation"] = problem.relation  # @property, not a dataclass field -- see _dataclass_to_dict's docstring
        result.append(item)
    return result


def _generate_evenodd_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min = params.get("a_min", DEFAULT_A_MIN)
    a_max = params.get("a_max", DEFAULT_A_MAX)
    nums_a = list(range(a_min, a_max + 1))
    problems = nuts_calc_tex.generate_evenodd_problems(nums_a, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_multiples_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min = params.get("a_min", DEFAULT_A_MIN)
    a_max = params.get("a_max", DEFAULT_A_MAX)
    if a_min < 1:
        raise ValueError("a_min must be at least 1 for the 'multiples' command.")

    multiples_count = params.get("multiples_count", nuts_calc_tex.DEFAULT_MULTIPLES_COUNT)
    if multiples_count < nuts_calc_tex.MIN_MULTIPLES_COUNT:
        raise ValueError(
            f"multiples_count must be at least {nuts_calc_tex.MIN_MULTIPLES_COUNT} for the 'multiples' command."
        )

    nums_a = list(range(a_min, a_max + 1))
    problems = nuts_calc_tex.generate_multiples_problems(nums_a, num, 1, multiples_count)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_divisors_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min = params.get("a_min", DEFAULT_A_MIN)
    a_max = params.get("a_max", DEFAULT_A_MAX)
    if a_min < 1:
        raise ValueError("a_min must be at least 1 for the 'divisors' command.")

    nums_a = list(range(a_min, a_max + 1))
    problems = nuts_calc_tex.generate_divisors_problems(nums_a, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_number_pair_problems(
    params: renderers.RendererRequest, num: int, compute: Callable[[int, int], int],
) -> list[dict[str, object]]:
    """
    Shared by 'lcm'/'gcd' (issue #172): math.lcm/math.gcd (via `compute`) is
    the only difference between the two, mirroring how
    nuts_calc_tex.py's own build_number_pair_pages() shares one function
    between the two CLI commands (nuts_calc_tex.py:3959-3969).
    """
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_number_pair_problems(compute, nums_a, nums_b, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_lcm_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    return _generate_number_pair_problems(params, num, math.lcm)


def _generate_gcd_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    return _generate_number_pair_problems(params, num, math.gcd)


def _generate_simplify_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "simplify")
    problems = nuts_calc_tex.generate_simplify_problems(numerator_digits, denominator_digits, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_commondenom_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "commondenom")
    problems = nuts_calc_tex.generate_commondenom_problems(numerator_digits, denominator_digits, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


def _generate_frac2dec_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    numerator_digits = params.get("numerator_digits", 1)
    denominator_digits = params.get("denominator_digits", 1)
    _validate_fraction_digits(numerator_digits, denominator_digits, "frac2dec")
    problems = nuts_calc_tex.generate_frac2dec_problems(numerator_digits, denominator_digits, num, 1)
    result = []
    for problem in problems:
        item = _dataclass_to_dict(problem)
        item["decimal_display"] = problem.decimal_display  # @property, not a dataclass field -- see _dataclass_to_dict's docstring
        result.append(item)
    return result


def _generate_dec2frac_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    problems = nuts_calc_tex.generate_dec2frac_problems(num, 1)
    result = []
    for problem in problems:
        item = _dataclass_to_dict(problem)
        item["decimal_display"] = problem.decimal_display
        result.append(item)
    return result


def _generate_divfrac_problems(params: renderers.RendererRequest, num: int) -> list[dict[str, object]]:
    a_min, a_max = resolve_digit_count_range(params, "a_digits", "a_min", "a_max", DEFAULT_A_MIN, DEFAULT_A_MAX)
    b_min, b_max = resolve_digit_count_range(params, "b_digits", "b_min", "b_max", DEFAULT_B_MIN, DEFAULT_B_MAX)
    if b_min < 1:
        raise ValueError("b_min must be at least 1 for the 'divfrac' command.")
    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    problems = nuts_calc_tex.generate_divfrac_problems(nums_a, nums_b, num, 1)
    return [_dataclass_to_dict(problem) for problem in problems]


# command_type -> generator dispatch table (issue #167's contract): each
# sub-issue of #166 adds one generator function and one entry here, without
# touching the shared if/elif chain generate_problems() used to have.
# `100` has no entry: it is handled by generate_hundred_square_table() and
# the endpoint's dedicated `command_type == '100'` branch, not this dispatch
# table, because its single-table `{"table": {...}}` contract does not fit
# the list-shaped generators collected here (issue #228). generate_problems()
# also raises a targeted ValueError for `100` pointing callers there.
_COMMAND_GENERATORS = {
    "com": _generate_com_problems,
    "99": _generate_kuku_problems,
    "aBc": _generate_abc_problems,
    "squ": _generate_squ_problems,
    "pi": _generate_pi_problems,
    "frac": _generate_frac_problems,
    "mixed": _generate_mixed_problems,
    "compare": _generate_compare_problems,
    "evenodd": _generate_evenodd_problems,
    "multiples": _generate_multiples_problems,
    "divisors": _generate_divisors_problems,
    "lcm": _generate_lcm_problems,
    "gcd": _generate_gcd_problems,
    "simplify": _generate_simplify_problems,
    "commondenom": _generate_commondenom_problems,
    "frac2dec": _generate_frac2dec_problems,
    "dec2frac": _generate_dec2frac_problems,
    "divfrac": _generate_divfrac_problems,
}
