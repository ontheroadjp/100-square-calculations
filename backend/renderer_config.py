"""Renderer selection for the Flask backend.

Resolves which renderer ``POST /generate-pdf`` / ``POST /generate-problems`` /
``GET /renderer-info`` should use (``NUTS_CALC_RENDERER``, default ``latex``) and
defines ``RendererRequest``, the shared ``TypedDict`` describing the JSON request
body those endpoints accept.

Until issue #297 this module also translated a ``RendererRequest`` into
``nuts_calc_tex.py`` CLI argv and ran it as a subprocess (``build_command`` /
``run``). That legacy ``/generate-pdf`` rendering path was removed once every
request was served in-process by ``backend/three_layer_renderer.py`` (issue #174
段3); ``reverse`` / ``merge`` / ``csv`` / ``debug`` stay on ``RendererRequest``
as reserved fields the 3-layer renderer does not honor.
"""

import os
from pathlib import Path
from typing import Literal, TypedDict


class RendererRequest(TypedDict, total=False):
    paper_size: str
    command_type: str
    a_value: int
    b_value: int
    a_digits: int
    b_digits: int
    a_min: int
    a_max: int
    b_min: int
    b_max: int
    result_max: int
    numerator_digits: int
    denominator_digits: int
    a_decimal_places: int
    b_decimal_places: int
    mixed_decimal_operand_order: bool
    decimal_places: int
    a_kind: list[str]
    b_kind: list[str]
    operator: list[str]
    carry_mode: Literal["required", "none", "mixed"]
    remainder_mode: Literal["required", "none", "mixed"]
    reducible_mode: Literal["required", "none", "mixed"]
    dividend_mode: Literal["integer", "decimal", "mixed"]
    descend: bool
    reverse: bool
    shuffle: bool
    intermediate: bool
    vertical: bool
    use_parentheses: bool
    missing_value: bool
    terms: int
    terms_min: int
    terms_max: int
    mixed_operators: bool
    same_denominator: bool
    different_denominators: bool
    proper_operands: bool
    proper_result: bool
    comparison_pattern: Literal["same-denominator", "same-numerator", "different-denominators"]
    a_fraction_form: Literal["proper", "improper", "mixed", "mix"]
    b_fraction_form: Literal["proper", "improper", "mixed", "mix"]
    rows: int
    columns: int
    with_bottom_answer: bool
    with_name_field: bool
    page: int
    merge: bool
    csv: bool
    debug: bool
    num: int  # problem_generation.py only: number of problems to generate (no PDF)


BACKEND_DIR = Path(__file__).resolve().parent

RENDERER_ENV_VAR = "NUTS_CALC_RENDERER"
DEFAULT_RENDERER = "latex"

RENDERER_SCRIPTS: dict[str, Path] = {
    "latex": BACKEND_DIR / "nuts_calc_tex.py",
}


def get_renderer_name() -> str:
    """
    Resolve which renderer to use from the `NUTS_CALC_RENDERER` environment
    variable, defaulting to `latex` (nuts_calc_tex.py) when the variable is
    unset. `latex` is currently the only renderer this mechanism can select
    (nuts_calc.py/`reportlab` was removed, issue #232); any other value,
    including an explicit `reportlab`, is rejected below by the same
    generic "unknown value" check that would reject any future typo or
    unsupported name, so a future second renderer can be added by adding
    an entry to `RENDERER_SCRIPTS` alone.
    """
    name = os.environ.get(RENDERER_ENV_VAR, DEFAULT_RENDERER)
    if name not in RENDERER_SCRIPTS:
        allowed = ", ".join(sorted(RENDERER_SCRIPTS))
        raise ValueError(
            f"Unknown {RENDERER_ENV_VAR} value {name!r}. Must be one of: {allowed}."
        )
    return name
