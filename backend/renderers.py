import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Literal, TypedDict


class RendererRequest(TypedDict, total=False):
    paper_size: str
    command_type: str
    a_value: int
    b_value: int
    a_min: int
    a_max: int
    b_min: int
    b_max: int
    numerator_digits: int
    denominator_digits: int
    a_decimal_places: int
    b_decimal_places: int
    decimal_places: int
    a_kind: list[str]
    b_kind: list[str]
    operator: list[str]
    carry_mode: Literal["required", "none", "mixed"]
    remainder_mode: Literal["required", "none", "mixed"]
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
    page: int
    merge: bool
    csv: bool
    debug: bool


BACKEND_DIR = Path(__file__).resolve().parent

RENDERER_ENV_VAR = "NUTS_CALC_RENDERER"
DEFAULT_RENDERER = "reportlab"

RENDERER_SCRIPTS: dict[str, Path] = {
    "reportlab": BACKEND_DIR / "nuts_calc.py",
    "latex": BACKEND_DIR / "nuts_calc_tex.py",
}

CARRY_MODE_FLAGS = {
    "required": "--carry-borrow",
    "none": "--no-carry-borrow",
    "mixed": "--mixed-carry-borrow",
}

REMAINDER_MODE_FLAGS = {
    "required": "--remainder",
    "none": "--no-remainder",
    "mixed": "--mixed-remainder",
}


def get_renderer_name() -> str:
    """
    Resolve which renderer to use from the `NUTS_CALC_RENDERER` environment
    variable, defaulting to `reportlab` (nuts_calc.py) to preserve existing
    behavior when the variable is unset.
    """
    name = os.environ.get(RENDERER_ENV_VAR, DEFAULT_RENDERER)
    if name not in RENDERER_SCRIPTS:
        allowed = ", ".join(sorted(RENDERER_SCRIPTS))
        raise ValueError(
            f"Unknown {RENDERER_ENV_VAR} value {name!r}. Must be one of: {allowed}."
        )
    return name


def build_command(renderer_name: str, params: RendererRequest, out_file: str) -> list[str]:
    """
    Translate a request's params into CLI arguments for the given renderer.

    nuts_calc.py and nuts_calc_tex.py share the same CLI argument surface
    (paper_size/command/-a/-b/--rows/--descend/etc.) with several
    exceptions that are latex-only -- nuts_calc.py does not accept any of
    them: `--vertical` (written-calculation / hissan format, issue #46),
    `--use-parentheses` (parenthesized "(a op1 b) op2 c" expressions, issue
    #67), `--missing-value` (missing-number "a op b = c" expressions with
    one operand boxed out, issue #69), `--terms`/`--terms-min`/
    `--terms-max`/`--mixed-operators` (N-term expressions with optional
    per-gap operator mixing, issue #71), and `--a-decimal-places`/
    `--b-decimal-places`/`--decimal-places`/`--a-kind`/`--b-kind` (decimal
    `ope` arithmetic and the `mixed` int/decimal/fraction command, issue
    #76). This command-building logic still translates all of these params
    unconditionally for both renderers; callers must only set them when the
    active renderer is `latex` (see `GET /renderer-info`), otherwise
    nuts_calc.py will reject the resulting CLI invocation as an unrecognized
    argument. `carry_mode` is likewise translated to the LaTeX-only
    `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` flags, and
    `remainder_mode` to the LaTeX-only `--remainder`/`--no-remainder`/
    `--mixed-remainder` flags (issue #91).
    """
    script_path = RENDERER_SCRIPTS[renderer_name]
    command = [sys.executable, str(script_path)]

    paper_size = params.get("paper_size")
    command_type = params.get("command_type")
    if not paper_size or not command_type:
        raise ValueError("Missing required parameters: paper_size or command_type")

    command.append(paper_size)
    command.append(command_type)

    if "a_value" in params:
        command.extend(["--a-value", str(params["a_value"])])
    if "b_value" in params:
        command.extend(["--b-value", str(params["b_value"])])
    if "a_min" in params:
        command.extend(["--a-min", str(params["a_min"])])
    if "a_max" in params:
        command.extend(["--a-max", str(params["a_max"])])
    if "b_min" in params:
        command.extend(["--b-min", str(params["b_min"])])
    if "b_max" in params:
        command.extend(["--b-max", str(params["b_max"])])
    if "numerator_digits" in params:
        command.extend(["--numerator-digits", str(params["numerator_digits"])])
    if "denominator_digits" in params:
        command.extend(["--denominator-digits", str(params["denominator_digits"])])
    if "a_decimal_places" in params:
        command.extend(["--a-decimal-places", str(params["a_decimal_places"])])
    if "b_decimal_places" in params:
        command.extend(["--b-decimal-places", str(params["b_decimal_places"])])
    if "decimal_places" in params:
        command.extend(["--decimal-places", str(params["decimal_places"])])
    if params.get("a_kind"):
        command.extend(["--a-kind", *params["a_kind"]])
    if params.get("b_kind"):
        command.extend(["--b-kind", *params["b_kind"]])
    if params.get("operator"):
        command.extend(["--operator", *params["operator"]])
    if "carry_mode" in params:
        carry_mode = params["carry_mode"]
        if carry_mode not in CARRY_MODE_FLAGS:
            allowed = ", ".join(CARRY_MODE_FLAGS)
            raise ValueError(f"Unknown carry_mode {carry_mode!r}. Must be one of: {allowed}.")
        command.append(CARRY_MODE_FLAGS[carry_mode])
    if "remainder_mode" in params:
        remainder_mode = params["remainder_mode"]
        if remainder_mode not in REMAINDER_MODE_FLAGS:
            allowed = ", ".join(REMAINDER_MODE_FLAGS)
            raise ValueError(f"Unknown remainder_mode {remainder_mode!r}. Must be one of: {allowed}.")
        command.append(REMAINDER_MODE_FLAGS[remainder_mode])
    if params.get("descend"):
        command.append("--descend")
    if params.get("reverse"):
        command.append("--reverse")
    if params.get("shuffle"):
        command.append("--shuffle")
    if params.get("intermediate"):
        command.append("--intermediate")
    if params.get("vertical"):
        command.append("--vertical")
    if params.get("use_parentheses"):
        command.append("--use-parentheses")
    if params.get("missing_value"):
        command.append("--missing-value")
    if "terms" in params:
        command.extend(["--terms", str(params["terms"])])
    if "terms_min" in params:
        command.extend(["--terms-min", str(params["terms_min"])])
    if "terms_max" in params:
        command.extend(["--terms-max", str(params["terms_max"])])
    if params.get("mixed_operators"):
        command.append("--mixed-operators")
    if params.get("same_denominator"):
        command.append("--same-denominator")
    if params.get("different_denominators"):
        command.append("--different-denominators")
    if params.get("proper_operands"):
        command.append("--proper-operands")
    if params.get("proper_result"):
        command.append("--proper-result")
    if "comparison_pattern" in params:
        command.extend(["--comparison-pattern", params["comparison_pattern"]])
    if "a_fraction_form" in params:
        command.extend(["--a-fraction-form", params["a_fraction_form"]])
    if "b_fraction_form" in params:
        command.extend(["--b-fraction-form", params["b_fraction_form"]])
    if "rows" in params:
        command.extend(["--rows", str(params["rows"])])
    if "columns" in params:
        command.extend(["--columns", str(params["columns"])])
    if params.get("with_bottom_answer"):
        command.append("--with-bottom-answer")
    if "page" in params:
        command.extend(["--page", str(params["page"])])
    if params.get("merge"):
        command.append("--merge")
    if params.get("csv"):
        command.append("--csv")
    if params.get("debug"):
        command.append("--debug")

    command.extend(["--out-file", out_file])
    return command


def run(
    params: RendererRequest, output_dir: str, renderer_name: str | None = None
) -> tuple[str, str, subprocess.CompletedProcess[str]]:
    """
    Generate a PDF via the selected renderer and return
    (filepath, filename, completed_process); the caller can inspect
    `completed_process.stdout`/`.stderr` for logging.

    Raises subprocess.CalledProcessError, FileNotFoundError, or ValueError
    on failure; the caller is responsible for translating those into an HTTP
    response.
    """
    renderer_name = renderer_name or get_renderer_name()
    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    command = build_command(renderer_name, params, output_filepath)
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    return output_filepath, output_filename, result
