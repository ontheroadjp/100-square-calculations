"""Flask-agnostic PDF generation glue for the internal presentation API.

This module owns the "3-layer model" worksheet-PDF pipeline (issue #183's
``build_presentation_document_tex`` / ``PresentationPage``): the 27
``_generate_*_pdf`` builders (including the multi-source ``review`` worksheet,
issue #140), the ``_is_*_request`` routing predicates, the
shared ``_resolve_page_count`` / ``_build_presentation_pages`` helpers, and the
``command_type`` -> builder dispatch. It was carved out of ``backend/app.py`` in
issue #290 (a strangler-fig step under #174) so ``app.py`` is reduced to HTTP
routing plus a thin renderer dispatcher.

It imports no ``flask`` and has no import-time side effects (no directory
creation): input is the request ``dict`` (``renderer_config.RendererRequest``), output
is a ``(filepath, filename)`` pair. This keeps it reusable by the CLI
(``nuts_calc_tex.py``), which is also planned to move onto the 3-layer model.

Every ``/generate-pdf`` request is served here. ``render_worksheet_pdf`` raises
``ValueError`` for a request no builder handles (an unmatched request is an
explicit HTTP 500). The legacy ``backend/renderers.py`` subprocess path and its
``app._USE_LEGACY_PDF_PIPELINE`` switch were removed in issue #297 (issue #174
段3); ``backend/renderer_config.py`` is now only renderer-name resolution plus
the shared ``RendererRequest`` type.
"""

import contextlib
import functools
import io
import math
import os
import random
import shutil
import uuid
from collections.abc import Callable
from typing import Protocol, TypeVar

import nuts_calc_tex
import problem_generation
import renderer_config

class _IndexedProblem(Protocol):
    index: int


_IndexedProblemT = TypeVar('_IndexedProblemT', bound=_IndexedProblem)


def _resolve_page_count(data: renderer_config.RendererRequest) -> int:
    page_count = int(data.get('page', 1))
    if page_count < 1:
        raise ValueError("page must be at least 1.")
    return page_count


# Command types whose slots are always short single-line equations, so the
# left-gutter number placement leaves a lopsided blank band on the right and
# an alternate placement reads better (issue #355). `ope` is checked
# separately because only its plain two-term variant qualifies.
_SHORT_SINGLE_LINE_COMMAND_TYPES = frozenset(
    {'99', 'squ', 'pi', 'com', 'evenodd', 'lcm', 'gcd'}
)
# `ope` flags/keys that break the plain two-term ``a op b =`` shape into
# something multi-line or widely variable in width per row -- a parentheses
# tree, vertical hissan, staged mental-arithmetic chain, missing-value blank,
# or a flat multi-term / mixed-operator expression. Any of them keeps the
# default gutter placement; everything else (operand magnitude, digit count,
# decimals, division-with-remainder, add/sub operator mix) is still one short
# line per row, so it takes the alternate placement (issue #355).
_OPE_WIDE_LAYOUT_FLAG_KEYS = (
    'use_parentheses', 'vertical', 'intermediate', 'missing_value', 'mixed_operators',
)
_OPE_MULTI_TERM_KEYS = ('terms', 'terms_min', 'terms_max')
# The alternate placement only helps a 1-2 column grid; 3+ columns already
# pack tightly.
_SHORT_DRILL_MAX_COLUMNS = 2
# Which non-default nuts_calc_tex.NumberPlacement the short single-line
# allowlist uses. Kept as one named constant so the choice is a single edit.
_SHORT_DRILL_NUMBER_PLACEMENT = 'inline'


def _ope_is_short_single_line(data: renderer_config.RendererRequest) -> bool:
    """Whether an `ope` request is a plain two-term ``a op b =`` equation (#355).

    Only the flags that make the row multi-line or widely variable in width
    disqualify it; operand size, digit count and decimals do not -- e.g. a
    grade-3 3-digit x 2-digit multiplication is still one short line.
    """
    if any(data.get(key) for key in _OPE_WIDE_LAYOUT_FLAG_KEYS):
        return False
    if any(key in data for key in _OPE_MULTI_TERM_KEYS):
        return False
    return True


def _resolve_number_placement(
    data: renderer_config.RendererRequest,
) -> nuts_calc_tex.NumberPlacement:
    """Pick the Layer 2 inline-slot number placement from the request (#355).

    The alternate placement for a 1-2 column grid of short single-line drills
    (so the columns are not lopsided to the left), the default ``gutter`` for
    everything else -- a conservative allowlist that keeps byte-identical
    output for every non-allowlisted command type and every `ope` variant.
    """
    if int(data.get('columns', 2)) > _SHORT_DRILL_MAX_COLUMNS:
        return nuts_calc_tex.DEFAULT_NUMBER_PLACEMENT
    command_type = data.get('command_type')
    is_short_single_line = command_type in _SHORT_SINGLE_LINE_COMMAND_TYPES or (
        command_type == 'ope' and _ope_is_short_single_line(data)
    )
    if not is_short_single_line:
        return nuts_calc_tex.DEFAULT_NUMBER_PLACEMENT
    return _SHORT_DRILL_NUMBER_PLACEMENT


def _build_presentation_pages(
    data: renderer_config.RendererRequest,
    order: int,
    generate_page: Callable[[int], list[_IndexedProblemT]],
    bottom_answer_builder: Callable[[list[_IndexedProblemT]], str] | None,
) -> list[nuts_calc_tex.PresentationPage[_IndexedProblemT]]:
    """Generate and decorate every requested worksheet page."""
    pages = []
    for page_number in range(1, _resolve_page_count(data) + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_page(start_index)
        bottom_answer_tex = (
            bottom_answer_builder(problems)
            if data.get('with_bottom_answer', False) and bottom_answer_builder is not None
            else None
        )
        pages.append(
            nuts_calc_tex.PresentationPage(
                problems=problems,
                indices=[problem.index for problem in problems],
                bottom_answer_tex=bottom_answer_tex,
            )
        )
    return pages


def _generate_com_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'com' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183) instead of shelling
    out through the legacy subprocess path (issue #199, the first
    command-group migration under #174/B-5). Basic-case only: a_value plus
    optional rows/columns, always a single blank (practice) page --
    with_bottom_answer/with_name_field/multi-page/merge are not wired for
    'com' yet (explicitly out of scope for #199).

    'com' reads a_value directly (it's always a literal value there, never a
    digit count -- issue #230). A future _generate_*_pdf-style builder for a
    command in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS (ope/100/lcm/gcd/
    divfrac) must instead resolve its range via
    problem_generation.resolve_digit_count_range(data, 'a_digits', 'a_min',
    'a_max', ...), not read a_value/a_digits directly like this function does.
    """
    target = problem_generation.validate_com_target(data.get('a_value'))

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_com_problems(
            target, rows * columns, start_index
        ),
        nuts_calc_tex.build_com_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_com_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # engine_adapter.compile() calls nuts_calc_tex.failure() on a LaTeX
    # compile error, which prints to stdout and raises SystemExit rather
    # than a normal Exception -- a design built for the CLI's subprocess
    # isolation (see LatexEngineAdapter.compile's docstring). Called
    # in-process here, an uncaught SystemExit would abort this request's
    # handling without a JSON response, so it must be caught and converted.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_plain_mixed_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """Return whether data selects the basic two-term mixed worksheet."""
    if data.get('command_type') != 'mixed':
        return False
    if data.get('mixed_operators'):
        return False
    return not any(key in data for key in ('terms', 'terms_min', 'terms_max'))


def _is_multi_term_mixed_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """Return whether data selects a multi-term or mixed-operator worksheet."""
    if data.get('command_type') != 'mixed' or data.get('reducible_mode') is not None:
        return False
    return bool(data.get('mixed_operators')) or any(
        key in data for key in ('terms', 'terms_min', 'terms_max')
    )


def _generate_mixed_pdf(
    data: renderer_config.RendererRequest,
    output_dir: str,
    *,
    terms_min: int = nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT,
    terms_max: int = nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT,
    mixed_operators: bool = False,
) -> tuple[str, str]:
    """Build a mixed PDF through the presentation API.

    Operand kinds, operator, fraction digit counts, and decimal places retain
    the CLI defaults when omitted. Reducibility variants require the same
    two-term fraction/integer and mul/div shape as the CLI.
    """
    numerator_digits = data.get('numerator_digits', 1)
    denominator_digits = data.get('denominator_digits', 1)
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'mixed' command."
            )

    decimal_places = data.get('decimal_places', 1)
    if not nuts_calc_tex.MIN_DECIMAL_PLACES <= decimal_places <= nuts_calc_tex.MAX_DECIMAL_PLACES:
        raise ValueError(
            f"decimal_places must be between {nuts_calc_tex.MIN_DECIMAL_PLACES} and "
            f"{nuts_calc_tex.MAX_DECIMAL_PLACES} for the 'mixed' command."
        )

    a_kinds = list(data.get('a_kind') or nuts_calc_tex.MIXED_OPERAND_KINDS)
    b_kinds = list(data.get('b_kind') or nuts_calc_tex.MIXED_OPERAND_KINDS)
    operators = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)
    valid_operand_kinds = set(nuts_calc_tex.MIXED_OPERAND_KINDS)
    if not set(a_kinds) <= valid_operand_kinds or not set(b_kinds) <= valid_operand_kinds:
        raise ValueError(
            f"a_kind and b_kind must contain only: {', '.join(nuts_calc_tex.MIXED_OPERAND_KINDS)}."
        )
    valid_operators = set(nuts_calc_tex.MIX_OPERATORS) | {'mix'}
    if not set(operators) <= valid_operators:
        raise ValueError(
            f"operator must contain only: {', '.join(sorted(valid_operators))}."
        )

    reducible_mode = data.get('reducible_mode')
    if reducible_mode is not None:
        if reducible_mode not in {'required', 'none', 'mixed'}:
            raise ValueError(
                "reducible_mode must be one of: mixed, none, required."
            )
        if not operators or not set(operators) <= {'mul', 'div'}:
            raise ValueError(
                "reducible_mode only supports 'mul'/'div' operators for the 'mixed' command."
            )
        if {tuple(a_kinds), tuple(b_kinds)} != {('fraction',), ('int',)}:
            raise ValueError(
                "reducible_mode requires exactly one a_kind=['fraction']/b_kind=['int'] pairing "
                "(in either order) for the 'mixed' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_mixed_problems(
            a_kinds, b_kinds, operators, mixed_operators,
            numerator_digits, denominator_digits, decimal_places,
            terms_min, terms_max, rows * columns, start_index,
            reducible_mode,
        ),
        nuts_calc_tex.build_mixed_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_mixed_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_multi_term_mixed_pdf(
    data: renderer_config.RendererRequest, output_dir: str
) -> tuple[str, str]:
    """Build a multi-term or mixed-operator mixed PDF via the presentation API."""
    terms = data.get('terms')
    terms_min = data.get('terms_min', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    terms_max = data.get('terms_max', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    if terms is not None:
        terms_min = terms_max = terms
    if terms_min > terms_max:
        raise ValueError("terms_min must be less than or equal to terms_max.")

    terms_min, terms_max = nuts_calc_tex.resolve_term_range(terms_min, terms_max, False)
    return _generate_mixed_pdf(
        data,
        output_dir,
        terms_min=terms_min,
        terms_max=terms_max,
        mixed_operators=bool(data.get('mixed_operators', False)),
    )


def _generate_lcm_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an 'lcm' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), mirroring
    _generate_com_pdf's pattern (issue #199) for #174(B-5)'s pattern-1a `lcm`
    migration (issue #211). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max) plus rows/columns -- always a single blank
    (practice) page. with_bottom_answer/with_name_field/multi-page/merge are
    unsupported here too, matching _generate_com_pdf's scope.

    'lcm' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS (unlike 'com'),
    so a/b are resolved via problem_generation.resolve_digit_count_range
    rather than read directly -- see _generate_com_pdf's docstring, and
    _generate_ope_pdf for the same resolution pattern. 'lcm' has no variant
    flags (vertical/intermediate/use_parentheses/etc. are all rejected by
    _init() for non-'ope' commands), so unlike the `ope` migrations this
    needs no `_is_lcm_pdf_request` helper -- a plain command_type equality
    check in generate_pdf() is enough, matching 'com'.
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_number_pair_problems(
            math.lcm, nums_a, nums_b, rows * columns, start_index
        ),
        nuts_calc_tex.build_number_pair_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_lcm_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_divfrac_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build a basic division-as-fraction PDF through the presentation API.

    The digit-count shorthand and explicit ranges retain the CLI contract.
    This basic-case migration produces one blank page; extended output fields
    remain on neither this in-process path nor its caller.
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    if b_min < 1:
        raise ValueError("b_min must be at least 1 for the 'divfrac' command.")

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_divfrac_problems(
            nums_a, nums_b, rows * columns, start_index
        ),
        nuts_calc_tex.build_divfrac_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_divfrac_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_approx_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build an 'approx' (概数 rounding / estimation, issue #346) PDF via the
    internal presentation API.

    `approx` is not a digit-count-shorthand command: operand ranges come
    straight from a_min/a_max (and b_min/b_max for estimate/quotient), and
    nuts_calc_tex.resolve_approx_params() fills the same kind-specific
    defaults and runs the same feasibility checks the CLI's _init() does,
    raising ValueError (mapped to HTTP 500 by app.py) on an invalid request.
    """
    operator_field = data.get('operator') or []
    params = nuts_calc_tex.resolve_approx_params(
        kind=str(data.get('kind', 'round')),
        round_method=str(data.get('round_method', 'round')),
        round_place=data.get('round_place'),
        sig_digits=data.get('sig_digits'),
        quotient_decimal_places=data.get('quotient_decimal_places'),
        dividend_decimal_places=data.get('dividend_decimal_places'),
        operator=operator_field[0] if operator_field else None,
        a_min=int(data.get('a_min', problem_generation.DEFAULT_A_MIN)),
        a_max=int(data.get('a_max', problem_generation.DEFAULT_A_MAX)),
        b_min=int(data.get('b_min', problem_generation.DEFAULT_B_MIN)),
        b_max=int(data.get('b_max', problem_generation.DEFAULT_B_MAX)),
    )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(params.a_min, params.a_max + 1))
    nums_b = list(range(params.b_min, params.b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_approx_problems(
            params.kind, params.round_method, params.sig_digits, params.round_place,
            params.operator, params.quotient_decimal_places, params.dividend_decimal_places,
            nums_a, nums_b, rows * columns, start_index,
        ),
        nuts_calc_tex.build_approx_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_approx_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_gcd_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'gcd' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), mirroring the pattern-1a
    `lcm` migration (issue #211) for issue #212. Basic-case only: a/b range
    (a_digits/b_digits or a_min/a_max/b_min/b_max) plus rows/columns -- always
    a single blank (practice) page. with_bottom_answer/with_name_field/
    multi-page/merge remain unsupported, matching the sibling migrations.

    Like 'lcm', 'gcd' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS, so
    a/b are resolved via problem_generation.resolve_digit_count_range. It has
    no variant flags, so an exact command_type equality check is sufficient.
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_number_pair_problems(
            math.gcd, nums_a, nums_b, rows * columns, start_index
        ),
        nuts_calc_tex.build_number_pair_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_gcd_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_evenodd_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an 'evenodd' command PDF via the internal presentation API (issue
    #214). Basic-case only: a_min/a_max plus optional rows/columns, always a
    single blank page. Answer pages, bottom answers, name fields, multiple
    pages, and merged output are not wired in this builder.
    """
    a_min = data.get('a_min', problem_generation.DEFAULT_A_MIN)
    a_max = data.get('a_max', problem_generation.DEFAULT_A_MAX)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_evenodd_problems(
            nums_a, rows * columns, start_index
        ),
        nuts_calc_tex.build_evenodd_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_evenodd_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_kuku_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a '99' (times-table / kuku) command PDF via nuts_calc_tex.py's
    internal presentation API (build_presentation_document_tex, issue #183),
    mirroring _generate_com_pdf's pattern (issue #199) for this pattern-1a
    migration (#208). Basic-case only: a_value plus optional rows/columns/
    descend/shuffle/reverse, always a single blank (practice) page
    (with_bottom_answer/with_name_field/multi-page/merge are not wired here,
    matching _generate_com_pdf's scope). descend/shuffle are
    supported (unlike the other omitted flags) because frontend/web's
    g2-kuku preset (drillPresets.js) sends them for its descending/random
    question-order settings; silently ignoring them here would regress that
    live feature once this command_type no longer had a legacy subprocess
    path to fall back to. `reverse` (issue #292) is the presentation-layer
    equation side-swap (`c = a x b`), bound into the content_format via
    functools.partial; it is distinct from the descend/shuffle data-layer
    ordering flags.

    '99' reads a_value directly like 'com' (it's always a literal value
    there, never a digit count -- issue #230); see
    problem_generation.validate_kuku_a_value's docstring for the shared
    validation this reuses.
    """
    a_value = problem_generation.validate_kuku_a_value(data.get('a_value'))
    descend = bool(data.get('descend', False))
    shuffle = bool(data.get('shuffle', False))
    reverse = bool(data.get('reverse', False))

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_kuku_problems(
            a_value, rows * columns, start_index, descend, shuffle
        ),
        nuts_calc_tex.build_kuku_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=functools.partial(
            nuts_calc_tex.build_kuku_slot_content_tex, reverse=reverse
        ),
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_abc_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a basic-case 'aBc' PDF via the internal presentation API.

    The migration intentionally covers one blank page with optional
    rows/columns only, matching #199's scope. Answer pages, bottom answers,
    name fields, multiple pages, and merged output remain on the legacy CLI
    path until those presentation features are migrated separately.
    """
    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_abc_problems(
            rows * columns, start_index
        ),
        nuts_calc_tex.build_abc_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_abc_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_pi_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'pi' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), mirroring
    _generate_com_pdf's pattern (issue #199) for the pattern-1a
    `99`/`squ`/`pi`/`lcm`/`gcd` migration group (issue #210). Basic-case
    only: a_value plus optional rows/columns/descend/shuffle/reverse, always
    a single blank (practice) page -- with_bottom_answer/with_name_field/
    multi-page/merge are not wired for 'pi' yet (explicitly out of scope for
    #210, matching _generate_com_pdf's scope). `reverse` (issue #292) is the
    presentation-layer equation side-swap (`c = a x 3.14`), bound into the
    content_format via functools.partial.

    'pi' reads a_value directly (like 'com', not a digit-count shorthand --
    see _generate_com_pdf's docstring).
    """
    start_num = problem_generation.validate_pi_start(data.get('a_value'))
    descend = bool(data.get('descend', False))
    shuffle = bool(data.get('shuffle', False))
    reverse = bool(data.get('reverse', False))

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_pi_problems(
            start_num, rows * columns, start_index, descend, shuffle
        ),
        nuts_calc_tex.build_pi_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=functools.partial(
            nuts_calc_tex.build_pi_slot_content_tex, reverse=reverse
        ),
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_plain_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the plain 2-term `ope` PDF this issue (#205,
    the first migration under the pattern-1a tracking issue #201) covers:
    the horizontal add/sub/mul/div/mix layout (build_horizontal_block_tex),
    with none of the flags that select a different content-format pattern
    or a different pattern-1a variant migrated separately --
    vertical(pattern 6)/intermediate(pattern 5)/use_parentheses(#206's tree
    variant, migrated by _is_tree_ope_pdf_request)/missing_value(pattern 2,
    #223's mushikuizan variant, migrated by
    _is_missing_value_ope_pdf_request)/the terms family
    (terms/terms_min/terms_max/mixed_operators, #207's flat multi-term
    variant, migrated by _is_multi_term_ope_pdf_request). Every other
    combination is rejected here (and by nuts_calc_tex.py's _init()
    validation), returning HTTP 500.
    """
    if data.get('command_type') != 'ope':
        return False
    if data.get('vertical') or data.get('intermediate'):
        return False
    if data.get('use_parentheses') or data.get('missing_value'):
        return False
    if data.get('mixed_operators'):
        return False
    if any(key in data for key in ('terms', 'terms_min', 'terms_max')):
        return False
    return True


def _generate_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a plain 2-term 'ope' command PDF via nuts_calc_tex.py's internal
    presentation API (build_presentation_document_tex, issue #183), mirroring
    _generate_com_pdf's pattern (issue #199) for the first pattern-1a
    migration (#201/#205). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max), operator, decimal places, carry_mode,
    remainder_mode, result_max, plus rows/columns -- always a single blank
    (practice) page. Callers must route here only when
    _is_plain_ope_pdf_request(data) is true; with_bottom_answer/
    with_name_field/multi-page/merge are unsupported here too, matching
    _generate_com_pdf's scope.

    'ope' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS (unlike 'com'),
    so a/b are resolved via problem_generation.resolve_digit_count_range
    rather than read directly (see _generate_com_pdf's docstring).
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)
    a_decimal_places = data.get('a_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES)
    b_decimal_places = data.get('b_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_ope_problems(
            nums_a, nums_b, operator, rows * columns, start_index,
            a_decimal_places, b_decimal_places,
            data.get('carry_mode'), data.get('remainder_mode'), data.get('result_max'),
            dividend_mode=data.get('dividend_mode'),
            a_multiple=data.get('a_multiple'), b_multiple=data.get('b_multiple'),
            quotient_digits=data.get('quotient_digits'),
            decimal_remainder=bool(data.get('decimal_remainder', False)),
            divide_through=bool(data.get('divide_through', False)),
        ),
        nuts_calc_tex.build_ope_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_tree_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the `ope --use-parentheses` ('tree' variant)
    PDF this issue (#206, following #205's plain 2-term migration under the
    pattern-1a tracking issue #201) covers: command_type == 'ope' with
    use_parentheses set, and none of vertical/intermediate/missing_value
    also set -- each is mutually exclusive with --use-parentheses per
    nuts_calc_tex.py's _init() validation (nuts_calc_tex.py:676-692), so a
    request combining them is invalid per that validation and returns HTTP
    500. The
    terms family (terms/terms_min/terms_max/mixed_operators) IS supported
    here: it is --use-parentheses's own N-term generalization (issue #71),
    not a separate pattern-1a-adjacent variant.
    """
    if data.get('command_type') != 'ope':
        return False
    if not data.get('use_parentheses'):
        return False
    if data.get('vertical') or data.get('intermediate') or data.get('missing_value'):
        return False
    return True


def _generate_tree_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an `ope --use-parentheses` (tree variant) command PDF via
    nuts_calc_tex.py's internal presentation API
    (build_presentation_document_tex, issue #183), mirroring
    _generate_ope_pdf's pattern (issue #205) for the pattern-1a tree-variant
    migration (#201/#206). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max), operator, mixed_operators, nontrivial_division
    (issue #342), the terms family (terms/terms_min/terms_max), result_max,
    plus rows/columns -- always a
    single blank (practice) page. Callers must route here only when
    _is_tree_ope_pdf_request(data) is true; with_bottom_answer/
    with_name_field/multi-page/merge are unsupported here too, matching
    _generate_ope_pdf's scope.

    'ope' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS, so a/b are
    resolved via problem_generation.resolve_digit_count_range (see
    _generate_com_pdf's docstring). terms_min/terms_max resolution mirrors
    problem_generation._determine_ope_variant's 'tree' branch (not called
    directly here since that function also covers the missing_value/
    multi_term branches this issue does not route to).
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)
    mixed_operators = bool(data.get('mixed_operators', False))
    nontrivial_division = bool(data.get('nontrivial_division', False))

    terms = data.get('terms')
    terms_min = data.get('terms_min', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    terms_max = data.get('terms_max', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    if terms is not None:
        terms_min = terms_max = terms
    if terms_min > terms_max:
        raise ValueError("terms_min must be less than or equal to terms_max.")
    terms_min, terms_max = nuts_calc_tex.resolve_term_range(terms_min, terms_max, use_parentheses=True)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_tree_ope_problems(
            nums_a, nums_b, operator, mixed_operators, terms_min, terms_max,
            rows * columns, start_index, data.get('result_max'), nontrivial_division,
        ),
        nuts_calc_tex.build_tree_ope_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_tree_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_multi_term_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the flat multi-term `ope` ('multi_term'
    variant, no parentheses) PDF this issue (#207, the last migration under
    the pattern-1a tracking issue #201, following #205's plain 2-term and
    #206's tree-variant migrations) covers: command_type == 'ope' with the
    terms family (terms/terms_min/terms_max/mixed_operators) requesting more
    than the plain 2-term shape, and none of
    vertical/intermediate/use_parentheses/missing_value also set (each
    selects a different content-format pattern or the tree variant already
    migrated separately). Mirrors nuts_calc_tex.py's
    _ope_uses_multi_term(ini) predicate (nuts_calc_tex.py:3091-3097), which
    the same request would hit inside build_ope_pages() on the subprocess
    path.
    """
    if data.get('command_type') != 'ope':
        return False
    if data.get('vertical') or data.get('intermediate'):
        return False
    if data.get('use_parentheses') or data.get('missing_value'):
        return False
    if data.get('mixed_operators'):
        return True
    return any(key in data for key in ('terms', 'terms_min', 'terms_max'))


def _generate_multi_term_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a flat multi-term 'ope' command PDF (no parentheses; terms/
    terms_min/terms_max/mixed_operators) via nuts_calc_tex.py's internal
    presentation API (build_presentation_document_tex, issue #183),
    mirroring _generate_tree_ope_pdf's pattern (issue #206) for the last
    pattern-1a migration (#201/#207). Basic-case only: a/b range
    (a_digits/b_digits or a_min/a_max/b_min/b_max), operator,
    mixed_operators, the terms family, result_max, plus rows/columns --
    always a single blank (practice) page. Callers must route here only
    when _is_multi_term_ope_pdf_request(data) is true; with_bottom_answer/
    with_name_field/multi-page/merge are unsupported here too, matching
    _generate_ope_pdf/_generate_tree_ope_pdf's scope.

    'ope' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS, so a/b are
    resolved via problem_generation.resolve_digit_count_range (see
    _generate_com_pdf's docstring). terms_min/terms_max resolution mirrors
    problem_generation._determine_ope_variant's 'multi_term' branch (not
    called directly here since that function also covers the tree/
    missing_value branches this issue does not route to) -- unlike
    _generate_tree_ope_pdf, resolve_term_range is called with
    use_parentheses=False (floor 2, not 3).
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)
    mixed_operators = bool(data.get('mixed_operators', False))

    terms = data.get('terms')
    terms_min = data.get('terms_min', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    terms_max = data.get('terms_max', nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT)
    if terms is not None:
        terms_min = terms_max = terms
    if terms_min > terms_max:
        raise ValueError("terms_min must be less than or equal to terms_max.")
    terms_min, terms_max = nuts_calc_tex.resolve_term_range(terms_min, terms_max, use_parentheses=False)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_multi_term_ope_problems(
            nums_a, nums_b, operator, mixed_operators, terms_min, terms_max,
            rows * columns, start_index, data.get('result_max'),
        ),
        nuts_calc_tex.build_multi_term_ope_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_multi_term_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_missing_value_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the `ope --missing-value` (mushikuizan) PDF this
    issue (#223, one of #174/B-5's breadth=1 pattern-2 batches, following the
    pattern-1a `ope` migrations #205/#206/#207) covers: command_type == 'ope'
    with missing_value set, and none of
    vertical/intermediate/use_parentheses/mixed_operators/the terms family
    also set -- each is mutually exclusive with --missing-value per
    nuts_calc_tex.py's _init() validation (nuts_calc_tex.py:684-715), so a
    request combining them is invalid per that validation and returns HTTP
    500.
    """
    if data.get('command_type') != 'ope':
        return False
    if not data.get('missing_value'):
        return False
    if data.get('vertical') or data.get('intermediate'):
        return False
    if data.get('use_parentheses') or data.get('mixed_operators'):
        return False
    if any(key in data for key in ('terms', 'terms_min', 'terms_max')):
        return False
    return True


def _generate_missing_value_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an `ope --missing-value` (mushikuizan) command PDF via
    nuts_calc_tex.py's internal presentation API
    (build_presentation_document_tex, issue #183), mirroring
    _generate_ope_pdf's pattern (issue #205) for #174/B-5's pattern-2
    migration (#223). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max), operator, result_max, plus rows/columns --
    always a single blank (practice) page. Callers must route here only when
    _is_missing_value_ope_pdf_request(data) is true; with_bottom_answer/
    with_name_field/multi-page/merge are unsupported here too, matching
    _generate_ope_pdf's scope.

    'ope' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS, so a/b are
    resolved via problem_generation.resolve_digit_count_range (see
    _generate_com_pdf's docstring). generate_missing_value_problems takes no
    carry/remainder/decimal parameters -- missing-value problems are
    integer-only (see MissingValueProblem's docstring) -- so unlike
    _generate_ope_pdf those options are not forwarded here.
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_missing_value_problems(
            nums_a, nums_b, operator, rows * columns, start_index, data.get('result_max'),
        ),
        nuts_calc_tex.build_missing_value_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_missing_value_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_vertical_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the `ope --vertical` (hissan / written-calculation)
    PDF this issue (#227, one of #174/B-5's breadth=1 pattern-6 batches,
    following the pattern-1a `ope` migrations #205/#206/#207 and the pattern-2
    `--missing-value` migration #223) covers: command_type == 'ope' with
    vertical set, and none of
    intermediate/use_parentheses/missing_value/mixed_operators/the terms family
    also set -- each is mutually exclusive with --vertical per nuts_calc_tex.py's
    _init() validation (nuts_calc_tex.py:754-795), so a request combining them
    is invalid per that validation and returns HTTP 500.

    Mirrors _is_plain_ope_pdf_request exactly, only with `vertical` required
    instead of rejected.
    """
    if data.get('command_type') != 'ope':
        return False
    if not data.get('vertical'):
        return False
    if data.get('intermediate') or data.get('use_parentheses') or data.get('missing_value'):
        return False
    if data.get('mixed_operators'):
        return False
    if any(key in data for key in ('terms', 'terms_min', 'terms_max')):
        return False
    return True


def _generate_vertical_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an `ope --vertical` (hissan) command PDF via nuts_calc_tex.py's
    internal presentation API (build_presentation_document_tex, issue #183),
    mirroring _generate_ope_pdf's pattern (issue #205) for #174/B-5's pattern-6
    migration (#227). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max), operator, decimal places, carry_mode,
    remainder_mode, result_max, plus rows/columns -- always a single blank
    (practice) page. Callers must route here only when
    _is_vertical_ope_pdf_request(data) is true; with_bottom_answer/
    with_name_field/multi-page/merge are unsupported here too, matching
    _generate_ope_pdf's scope.

    The written-calculation body is drawn by xlop (add/sub/mul) / longdivision
    (div); its multi-row output uses grid_layout='tabular' (the same grid the
    legacy CLI --vertical path uses, build_ope_page_pair's layout='tabular')
    rather than the default inline grid. The Layer-3 content format is
    build_vertical_ope_slot_content_tex (issue #227), composed with the Layer-2
    numbered content area.

    `--vertical` div requires an integer divisor (longdivision's
    `\\intlongdivision`), so a decimal `b_decimal_places` divisor is rejected
    here with the same message nuts_calc_tex.py's _init() uses
    (nuts_calc_tex.py:900-912) -- app.py bypasses _init(), so that check is
    re-implemented rather than inherited. `--vertical` + equal decimal places is
    otherwise allowed (issue #134).
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or problem_generation.DEFAULT_OPERATOR)
    a_decimal_places = data.get('a_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES)
    b_decimal_places = data.get('b_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES)

    if 'div' in operator and b_decimal_places > nuts_calc_tex.MIN_DECIMAL_PLACES:
        raise ValueError(
            "--vertical does not yet support a decimal --b-decimal-places "
            "divisor for the 'div' operator (see the open question in "
            "nuts_calc_tex.py.md)."
        )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_ope_problems(
            nums_a, nums_b, operator, rows * columns, start_index,
            a_decimal_places, b_decimal_places,
            data.get('carry_mode'), data.get('remainder_mode'), data.get('result_max'),
        ),
        nuts_calc_tex.build_ope_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_vertical_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        grid_layout='tabular',
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _is_intermediate_ope_pdf_request(data: renderer_config.RendererRequest) -> bool:
    """
    True when `data` requests the `ope --intermediate` (staged mental-math
    arrow-chain) PDF this issue (#226, one of #174/B-5's breadth=1 pattern-5
    batches, following the pattern-1a `ope` migrations #205/#206/#207 and the
    pattern-2 `--missing-value` migration #223) covers: command_type == 'ope'
    with intermediate set, and none of
    vertical/use_parentheses/missing_value/mixed_operators/the terms family
    also set -- each is mutually exclusive with --intermediate per
    nuts_calc_tex.py's _init() validation (nuts_calc_tex.py:750-797), so a
    request combining them is invalid per that validation and returns HTTP 500.
    """
    if data.get('command_type') != 'ope':
        return False
    if not data.get('intermediate'):
        return False
    if data.get('vertical') or data.get('use_parentheses') or data.get('missing_value'):
        return False
    if data.get('mixed_operators'):
        return False
    if any(key in data for key in ('terms', 'terms_min', 'terms_max')):
        return False
    return True


def _generate_intermediate_ope_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an `ope --intermediate` (staged mental-math arrow-chain) command PDF
    via nuts_calc_tex.py's internal presentation API
    (build_presentation_document_tex, issue #183), mirroring _generate_ope_pdf's
    pattern (issue #205) for #174/B-5's pattern-5 migration (#226). Basic-case
    only: a/b range (a_digits/b_digits or a_min/a_max/b_min/b_max), result_max,
    plus rows/columns -- always a single blank (practice) page. Callers must
    route here only when _is_intermediate_ope_pdf_request(data) is true;
    with_bottom_answer/with_name_field/multi-page/merge are unsupported here
    too, matching _generate_ope_pdf's scope.

    'ope' is in nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS, so a/b are
    resolved via problem_generation.resolve_digit_count_range (see
    _generate_com_pdf's docstring). --intermediate only supports a single
    'mul' operator and a single-digit second operand, and rejects decimal
    places (nuts_calc_tex.py:750-797, 880-881); the same constraints are
    enforced here with ValueError so an out-of-scope request fails explicitly
    rather than silently producing a different worksheet. carry_mode/remainder_mode/decimal places are not forwarded --
    they are meaningless for a mul-only variant (cf. _generate_missing_value_ope_pdf).
    """
    a_min, a_max = problem_generation.resolve_digit_count_range(
        data, 'a_digits', 'a_min', 'a_max',
        problem_generation.DEFAULT_A_MIN, problem_generation.DEFAULT_A_MAX,
    )
    b_min, b_max = problem_generation.resolve_digit_count_range(
        data, 'b_digits', 'b_min', 'b_max',
        problem_generation.DEFAULT_B_MIN, problem_generation.DEFAULT_B_MAX,
    )
    operator = list(data.get('operator') or ['mul'])
    if operator != ['mul']:
        raise ValueError("--intermediate only supports a single 'mul' operator (use -o mul).")
    if b_max > nuts_calc_tex.INTERMEDIATE_SINGLE_DIGIT_MAX:
        raise ValueError(
            "--intermediate only supports a single-digit second operand (use -b 1 or --b-max <= 9)."
        )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_ope_problems(
            nums_a, nums_b, operator, rows * columns, start_index,
            result_max=data.get('result_max'),
        ),
        nuts_calc_tex.build_ope_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_intermediate_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_squ_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'squ' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), following #199's
    'com' precedent (issue #209, tracked under #174/B-5's remaining
    pattern-1a migrations #208/#209/#210/#211/#212). Basic-case only:
    a_value plus optional rows/columns/descend/shuffle/reverse, always a
    single blank (practice) page -- with_bottom_answer/with_name_field/
    multi-page/merge are not wired for 'squ' yet (explicitly out of scope
    for #209, matching #199's scope). descend/shuffle are read from `data`
    and forwarded to generate_squ_problems (issue #298), matching the
    _generate_kuku_pdf / _generate_pi_pdf helpers; they are the data-layer
    ordering flags, distinct from the presentation-layer `reverse` flag.
    `reverse` (issue #292) is the presentation-layer equation side-swap
    (`c = a x a`), bound into the content_format via functools.partial.

    'squ' reads a_value directly (it's always a literal starting square
    number, never a digit count -- like 'com', unlike
    nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS).
    """
    start_num = problem_generation.validate_squ_start(data.get('a_value'))
    descend = bool(data.get('descend', False))
    shuffle = bool(data.get('shuffle', False))
    reverse = bool(data.get('reverse', False))

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_squ_problems(
            start_num, rows * columns, start_index, descend, shuffle
        ),
        nuts_calc_tex.build_squ_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=functools.partial(
            nuts_calc_tex.build_squ_slot_content_tex, reverse=reverse
        ),
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) rather than a normal
    # exception on a LaTeX compile error, which must be caught and converted
    # here so this in-process request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_multiples_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank `multiples` page via the internal presentation API.

    This basic-case migration preserves the data-layer defaults and the
    existing multiples-count semantics. Answer pages, bottom answers, name
    fields, multiple pages, and merged output are not wired in this builder.
    """
    a_min = int(data.get('a_min', problem_generation.DEFAULT_A_MIN))
    a_max = int(data.get('a_max', problem_generation.DEFAULT_A_MAX))
    if a_min < 1:
        raise ValueError("a_min must be at least 1 for the 'multiples' command.")

    multiples_count = int(data.get('multiples_count', nuts_calc_tex.DEFAULT_MULTIPLES_COUNT))
    if multiples_count < nuts_calc_tex.MIN_MULTIPLES_COUNT:
        raise ValueError(
            f"multiples_count must be at least {nuts_calc_tex.MIN_MULTIPLES_COUNT} "
            "for the 'multiples' command."
        )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_multiples_problems(
            nums_a, rows * columns, start_index, multiples_count
        ),
        nuts_calc_tex.build_multiples_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_multiples_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_divisors_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank `divisors` page via the internal presentation API.

    This basic-case migration preserves the data-layer range defaults.
    Answer pages, bottom answers, name fields, multiple pages, and merged
    output are not wired in this builder.
    """
    a_min = int(data.get('a_min', problem_generation.DEFAULT_A_MIN))
    a_max = int(data.get('a_max', problem_generation.DEFAULT_A_MAX))
    if a_min < 1:
        raise ValueError("a_min must be at least 1 for the 'divisors' command.")

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    nums_a = list(range(a_min, a_max + 1))
    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_divisors_problems(
            nums_a, rows * columns, start_index
        ),
        nuts_calc_tex.build_divisors_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_divisors_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_frac_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `frac` page via the presentation API."""
    numerator_digits = int(data.get('numerator_digits', 1))
    denominator_digits = int(data.get('denominator_digits', 1))
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'frac' command."
            )

    same_denominator = bool(data.get('same_denominator', False))
    different_denominators = bool(data.get('different_denominators', False))
    if same_denominator and different_denominators:
        raise ValueError("same_denominator and different_denominators cannot be combined.")

    proper_operands = bool(data.get('proper_operands', False))
    if proper_operands and numerator_digits > denominator_digits:
        raise ValueError(
            "proper_operands requires numerator_digits to be no greater than denominator_digits."
        )
    proper_result = bool(data.get('proper_result', False))

    operators = list(data.get('operator') or ['add'])
    allowed_operators = {'add', 'sub', 'mul', 'div', 'mix'}
    if not set(operators) <= allowed_operators:
        raise ValueError("operator contains an unsupported value for the 'frac' command.")

    a_fraction_form = data.get('a_fraction_form', 'proper')
    b_fraction_form = data.get('b_fraction_form', 'proper')
    allowed_fraction_forms = {'proper', 'mixed', 'mix'}
    if a_fraction_form not in allowed_fraction_forms or b_fraction_form not in allowed_fraction_forms:
        raise ValueError(
            "a_fraction_form/b_fraction_form do not support 'improper' or unknown forms "
            "for the 'frac' command."
        )
    if (a_fraction_form, b_fraction_form) != ('proper', 'proper') and operators not in (
        ['add'], ['sub']
    ):
        raise ValueError(
            "a_fraction_form/b_fraction_form require operator=['add'] or "
            "operator=['sub'] for the 'frac' command."
        )

    reducible_mode = data.get('reducible_mode')
    if reducible_mode is not None:
        if reducible_mode not in {'required', 'none', 'mixed'}:
            raise ValueError("Unknown reducible_mode for the 'frac' command.")
        if not operators or not set(operators) <= {'mul', 'div'}:
            raise ValueError(
                "reducible_mode only supports 'mul'/'div' operators for the 'frac' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_fraction_problems(
            numerator_digits,
            denominator_digits,
            operators,
            rows * columns,
            start_index,
            same_denominator,
            proper_operands,
            proper_result,
            different_denominators,
            a_fraction_form,
            b_fraction_form,
            reducible_mode,
        ),
        nuts_calc_tex.build_fraction_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_fraction_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_simplify_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `simplify` page via the presentation API."""
    numerator_digits = int(data.get('numerator_digits', 1))
    denominator_digits = int(data.get('denominator_digits', 1))
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'simplify' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_simplify_problems(
            numerator_digits, denominator_digits, rows * columns, start_index
        ),
        nuts_calc_tex.build_simplify_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_simplify_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_frac2dec_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `frac2dec` page via the presentation API."""
    numerator_digits = int(data.get('numerator_digits', 1))
    denominator_digits = int(data.get('denominator_digits', 1))
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'frac2dec' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_frac2dec_problems(
            numerator_digits, denominator_digits, rows * columns, start_index
        ),
        nuts_calc_tex.build_frac2dec_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_frac2dec_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_dec2frac_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `dec2frac` page via the presentation API.

    Unlike `frac2dec`, `dec2frac` has no numerator/denominator digit options --
    `generate_dec2frac_problems` takes only `(order, start_index)` -- so only
    `rows`/`columns` are validated here.
    """
    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_dec2frac_problems(
            rows * columns, start_index
        ),
        nuts_calc_tex.build_dec2frac_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_dec2frac_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_compare_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `compare` (fraction comparison) page via the
    presentation API (build_presentation_document_tex, issue #224 -- one of
    #174/B-5's breadth=1 pattern-3 batches, following #199's `com` precedent).

    `compare` shares `--numerator-digits`/`--denominator-digits` with
    `frac`/`simplify`/`frac2dec` and is NOT a DIGIT_COUNT_SHORTHAND_COMMANDS
    command, so those are read straight from `data` with the
    MIN_FRACTION_DIGITS..MAX_FRACTION_DIGITS check (like _generate_simplify_pdf).
    Basic case only: the comparison pattern / fraction forms / operand kinds
    use the CLI defaults (different-denominators, proper, proper,
    fraction-vs-fraction); with_bottom_answer/with_name_field/multi-page/
    merge/show_answer are out of scope, matching #199/#222.
    """
    numerator_digits = int(data.get('numerator_digits', 1))
    denominator_digits = int(data.get('denominator_digits', 1))
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'compare' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_fraction_comparison_problems(
            'different-denominators', 'proper', 'proper',
            numerator_digits, denominator_digits, rows * columns, start_index,
        ),
        None,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_fraction_comparison_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_commondenom_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank basic `commondenom` page via the presentation API."""
    numerator_digits = int(data.get('numerator_digits', 1))
    denominator_digits = int(data.get('denominator_digits', 1))
    for option_name, value in (
        ('numerator_digits', numerator_digits),
        ('denominator_digits', denominator_digits),
    ):
        if not nuts_calc_tex.MIN_FRACTION_DIGITS <= value <= nuts_calc_tex.MAX_FRACTION_DIGITS:
            raise ValueError(
                f"{option_name} must be between {nuts_calc_tex.MIN_FRACTION_DIGITS} and "
                f"{nuts_calc_tex.MAX_FRACTION_DIGITS} for the 'commondenom' command."
            )

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = _build_presentation_pages(
        data,
        rows * columns,
        lambda start_index: nuts_calc_tex.generate_commondenom_problems(
            numerator_digits, denominator_digits, rows * columns, start_index
        ),
        nuts_calc_tex.build_commondenom_bottom_answer_tex,
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_commondenom_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def _generate_hundred_square_pdf(data: renderer_config.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build one blank `100` (hundred-square addition table) page via the
    internal presentation API (build_presentation_document_tex, issue #183),
    for issue #229's migration of `command_type == '100'` off the legacy
    subprocess path.

    Unlike every other migrated command, `100` is one self-contained table
    per page with no per-problem numbering, so it uses the second Layer-2
    variant: ContentAreaLayout(numbered=False) (a single unnumbered
    full-content-area slot) plus grid_layout='block', matching the legacy
    build_hundred_square_pages() Page(columns=1, layout='block'). The Layer-3
    content format build_hundred_square_slot_content_tex ports the existing
    grid visuals as-is (guidelines-doc macro retrofit is #185/#270).

    The a/b axis ranges are resolved and range-checked by
    problem_generation.resolve_hundred_square_axes, shared with the
    `/generate-problems` `100` path (issue #228). Basic case only: always a
    single blank (practice) page -- show_answer / merge / multi-page / the
    `page` count are not wired here, matching the other _generate_*_pdf
    builders.
    """
    nums_left, nums_top = problem_generation.resolve_hundred_square_axes(data)

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages = [
        nuts_calc_tex.PresentationPage(
            problems=[nuts_calc_tex.generate_hundred_square(nums_left, nums_top)],
            indices=[page_number],
        )
        for page_number in range(1, _resolve_page_count(data) + 1)
    ]
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_hundred_square_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=1, columns=1, numbered=False),
        engine_adapter=engine_adapter,
        show_answer=False,
        grid_layout='block',
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


# Raised by render_worksheet_pdf when a `mixed` request combines reducible_mode
# with a multi-term / mixed_operators option: both `_is_*_mixed_pdf_request`
# predicates reject it, and nuts_calc_tex.py's _init() (nuts_calc_tex.py:843-848)
# rejects the same combination -- there is no valid worksheet for it.
_MIXED_REDUCIBLE_MULTI_TERM_ERROR = (
    "reducible_mode cannot be combined with terms/terms_min/terms_max/"
    "mixed_operators for the 'mixed' command."
)

# Raised by render_worksheet_pdf for any other request no builder handles
# (in practice only an unknown command_type, since every known one is covered).
_UNSUPPORTED_REQUEST_ERROR = (
    "No presentation-layer builder handles this /generate-pdf request "
    "(command_type={command_type!r})."
)


# --- review (multi-source 総合 worksheet, issue #140) ------------------------
#
# A review worksheet interleaves problems from several distinct drills onto
# one page. The composition (generate each source, concatenate, optionally
# shuffle, renumber, render through one kind-dispatching content format)
# lives here rather than in nuts_calc_tex.py so the CLI is untouched; the
# recipe (which sources, how many of each) is the caller's -- frontend/web's
# per-grade preset. Only the source command types the grade-3 prototype
# recipe needs are supported; adding a later grade whose recipe needs
# another drill means adding its generator here and its slot formatter to
# nuts_calc_tex.build_review_slot_content_tex.


def _review_ope_problems(
    source: dict[str, object], count: int
) -> list[nuts_calc_tex.ReviewProblem]:
    """Generate `count` plain 2-term `ope` problems for one review source.

    A trimmed counterpart to _generate_ope_pdf's parameter resolution:
    review sources pass explicit a_min/a_max/b_min/b_max (no a_digits
    shorthand) and only the options the grade-3 recipe uses.
    """
    a_min = int(source.get('a_min', problem_generation.DEFAULT_A_MIN))
    a_max = int(source.get('a_max', problem_generation.DEFAULT_A_MAX))
    b_min = int(source.get('b_min', problem_generation.DEFAULT_B_MIN))
    b_max = int(source.get('b_max', problem_generation.DEFAULT_B_MAX))
    operator = list(source.get('operator') or problem_generation.DEFAULT_OPERATOR)
    a_decimal_places = int(source.get('a_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES))
    b_decimal_places = int(source.get('b_decimal_places', nuts_calc_tex.MIN_DECIMAL_PLACES))
    problems = nuts_calc_tex.generate_ope_problems(
        list(range(a_min, a_max + 1)),
        list(range(b_min, b_max + 1)),
        operator,
        count,
        1,
        a_decimal_places,
        b_decimal_places,
        source.get('carry_mode'),
        source.get('remainder_mode'),
        source.get('result_max'),
    )
    return [
        nuts_calc_tex.ReviewProblem(index=problem.index, kind='ope', payload=problem)
        for problem in problems
    ]


def _review_frac_problems(
    source: dict[str, object], count: int
) -> list[nuts_calc_tex.ReviewProblem]:
    """Generate `count` basic `frac` add/sub problems for one review source."""
    numerator_digits = int(source.get('numerator_digits', 1))
    denominator_digits = int(source.get('denominator_digits', 1))
    operators = list(source.get('operator') or ['add'])
    problems = nuts_calc_tex.generate_fraction_problems(
        numerator_digits,
        denominator_digits,
        operators,
        count,
        1,
        bool(source.get('same_denominator', False)),
        bool(source.get('proper_operands', False)),
        bool(source.get('proper_result', False)),
    )
    return [
        nuts_calc_tex.ReviewProblem(index=problem.index, kind='frac', payload=problem)
        for problem in problems
    ]


_REVIEW_SOURCE_GENERATORS: dict[
    str, Callable[[dict[str, object], int], list[nuts_calc_tex.ReviewProblem]]
] = {
    'ope': _review_ope_problems,
    'frac': _review_frac_problems,
}

_REVIEW_UNSUPPORTED_SOURCE_ERROR = (
    "review worksheet source command_type {command_type!r} is not supported; "
    "supported: {supported}."
)


def _resolve_review_sources(
    data: renderer_config.RendererRequest,
) -> list[dict[str, object]]:
    """Validate `data['sources']` and return it as a list of source dicts."""
    sources = data.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError("review worksheet requires a non-empty 'sources' list.")
    resolved: list[dict[str, object]] = []
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("each review 'sources' entry must be an object.")
        command_type = source.get('command_type')
        if command_type not in _REVIEW_SOURCE_GENERATORS:
            raise ValueError(
                _REVIEW_UNSUPPORTED_SOURCE_ERROR.format(
                    command_type=command_type,
                    supported=", ".join(sorted(_REVIEW_SOURCE_GENERATORS)),
                )
            )
        num = source.get('num')
        if not isinstance(num, int) or isinstance(num, bool) or num < 1:
            raise ValueError("each review 'sources' entry needs an integer num >= 1.")
        resolved.append(source)
    return resolved


def _distribute_review_counts(weights: list[int], order: int) -> list[int]:
    """Split `order` grid slots across sources in proportion to `weights`.

    `num` on each source is a relative weight, so the page grid is always
    exactly filled whatever `rows * columns` is (e.g. the 10 / 20 / 30
    problem-count choice in frontend/web). When the weights already sum to
    `order` -- the documented common case -- every source gets exactly its
    weight back. Leftover slots from integer division go to the largest
    fractional remainders (largest-remainder method).
    """
    total_weight = sum(weights)
    if total_weight <= 0:
        # _resolve_review_sources already enforces num >= 1 per source, so
        # this only guards a direct caller passing all-zero weights.
        raise ValueError("review 'sources' need at least one positive num.")
    exact = [order * weight / total_weight for weight in weights]
    counts = [int(value) for value in exact]
    leftover = order - sum(counts)
    by_remainder = sorted(
        range(len(weights)), key=lambda i: exact[i] - counts[i], reverse=True
    )
    for i in by_remainder[:leftover]:
        counts[i] += 1
    return counts


def _generate_review_pdf(
    data: renderer_config.RendererRequest, output_dir: str
) -> tuple[str, str]:
    """Build a multi-source 'review' (総合) worksheet PDF (issue #140).

    Each `data['sources']` entry is generated by its own drill's data-layer
    function, the results are concatenated, optionally shuffled
    (deterministically when `review_seed` is given), renumbered 1..N per
    page, and rendered onto one page grid via a `kind`-dispatching content
    format (nuts_calc_tex.build_review_slot_content_tex). Basic-case only,
    mirroring the other _generate_*_pdf builders: a blank page per `page`,
    with_name_field honored, no bottom-answer / merge. Source `num` values
    are relative weights (see _distribute_review_counts), so the grid is
    always exactly filled for any rows * columns.
    """
    sources = _resolve_review_sources(data)

    rows = int(data.get('rows', nuts_calc_tex.DEFAULT_ROWS))
    columns = int(data.get('columns', 2))
    if rows < nuts_calc_tex.MIN_ROWS_OR_COLUMNS or columns < nuts_calc_tex.MIN_ROWS_OR_COLUMNS:
        raise ValueError(
            f"rows and columns must be at least {nuts_calc_tex.MIN_ROWS_OR_COLUMNS}."
        )
    order = rows * columns
    counts = _distribute_review_counts([int(source['num']) for source in sources], order)

    engine_adapter = nuts_calc_tex.get_latex_engine_adapter()
    if shutil.which(engine_adapter.binary_name) is None:
        raise ValueError(
            f"{engine_adapter.binary_name} not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    shuffle = bool(data.get('shuffle', False))
    rng = random.Random(data.get('review_seed')) if shuffle else None

    pages = []
    for page_number in range(1, _resolve_page_count(data) + 1):
        problems = []
        for source, count in zip(sources, counts):
            if count < 1:
                continue
            generator = _REVIEW_SOURCE_GENERATORS[source['command_type']]
            problems.extend(generator(source, count))
        if rng is not None:
            rng.shuffle(problems)
        start_index = (page_number - 1) * order + 1
        for offset, problem in enumerate(problems):
            problem.index = start_index + offset
        pages.append(
            nuts_calc_tex.PresentationPage(
                problems=problems,
                indices=[problem.index for problem in problems],
                bottom_answer_tex=None,
            )
        )

    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=pages,
        content_format=nuts_calc_tex.build_review_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns, number_placement=_resolve_number_placement(data)),
        engine_adapter=engine_adapter,
        show_answer=False,
        with_name_field=bool(data.get('with_name_field', False)),
    )

    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(output_dir, output_filename)

    # See _generate_com_pdf's matching comment: engine_adapter.compile()
    # raises SystemExit (via nuts_calc_tex.failure()) on a LaTeX compile
    # error, which must be caught and converted here so this in-process
    # request handler still returns a JSON response.
    captured_stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout):
            engine_adapter.compile(tex_source, output_filepath)
    except SystemExit as e:
        error_reason = captured_stdout.getvalue().strip() or "PDF compilation failed"
        raise RuntimeError(f'PDF generation failed: {error_reason}') from e

    return output_filepath, output_filename


def render_worksheet_pdf(
    data: renderer_config.RendererRequest, output_dir: str
) -> tuple[str, str]:
    """Render a worksheet PDF through the internal presentation API.

    Returns ``(filepath, filename)`` when ``data`` selects one of the covered
    builders. Raises ``ValueError`` when no builder matches -- every
    ``/generate-pdf`` request goes through this function (the legacy subprocess
    path was removed in issue #297), so an unmatched request is an explicit
    error rather than a silent subprocess fallthrough. The branch order here
    mirrors the dispatch ladder that lived in ``app.py``'s ``generate_pdf()``
    before issue #290 exactly, so which requests are served vs rejected is
    unchanged.

    The only recognized-``command_type`` request that reaches the terminal
    ``raise`` is ``mixed`` combined with ``reducible_mode`` and a
    multi-term / ``mixed_operators`` option -- an invalid combination
    ``nuts_calc_tex.py``'s ``_init()`` (nuts_calc_tex.py:843-848) also rejects
    outright. Every other unmatched request has an unknown ``command_type``.
    """
    if data.get('command_type') == 'review':
        return _generate_review_pdf(data, output_dir)
    if data.get('command_type') == 'com':
        return _generate_com_pdf(data, output_dir)
    if data.get('command_type') == 'lcm':
        return _generate_lcm_pdf(data, output_dir)
    if data.get('command_type') == 'divfrac':
        return _generate_divfrac_pdf(data, output_dir)
    if data.get('command_type') == 'approx':
        return _generate_approx_pdf(data, output_dir)
    if data.get('command_type') == 'gcd':
        return _generate_gcd_pdf(data, output_dir)
    if data.get('command_type') == 'evenodd':
        return _generate_evenodd_pdf(data, output_dir)
    if data.get('command_type') == '99':
        return _generate_kuku_pdf(data, output_dir)
    if data.get('command_type') == 'aBc':
        return _generate_abc_pdf(data, output_dir)
    if data.get('command_type') == 'pi':
        return _generate_pi_pdf(data, output_dir)
    if data.get('command_type') == '100':
        return _generate_hundred_square_pdf(data, output_dir)
    if _is_plain_mixed_pdf_request(data):
        return _generate_mixed_pdf(data, output_dir)
    if _is_multi_term_mixed_pdf_request(data):
        return _generate_multi_term_mixed_pdf(data, output_dir)
    if _is_plain_ope_pdf_request(data):
        return _generate_ope_pdf(data, output_dir)
    if _is_tree_ope_pdf_request(data):
        return _generate_tree_ope_pdf(data, output_dir)
    if _is_multi_term_ope_pdf_request(data):
        return _generate_multi_term_ope_pdf(data, output_dir)
    if _is_missing_value_ope_pdf_request(data):
        return _generate_missing_value_ope_pdf(data, output_dir)
    if _is_vertical_ope_pdf_request(data):
        return _generate_vertical_ope_pdf(data, output_dir)
    if _is_intermediate_ope_pdf_request(data):
        return _generate_intermediate_ope_pdf(data, output_dir)
    if data.get('command_type') == 'squ':
        return _generate_squ_pdf(data, output_dir)
    if data.get('command_type') == 'multiples':
        return _generate_multiples_pdf(data, output_dir)
    if data.get('command_type') == 'divisors':
        return _generate_divisors_pdf(data, output_dir)
    if data.get('command_type') == 'frac':
        return _generate_frac_pdf(data, output_dir)
    if data.get('command_type') == 'simplify':
        return _generate_simplify_pdf(data, output_dir)
    if data.get('command_type') == 'frac2dec':
        return _generate_frac2dec_pdf(data, output_dir)
    if data.get('command_type') == 'dec2frac':
        return _generate_dec2frac_pdf(data, output_dir)
    if data.get('command_type') == 'compare':
        return _generate_compare_pdf(data, output_dir)
    if data.get('command_type') == 'commondenom':
        return _generate_commondenom_pdf(data, output_dir)
    if data.get('command_type') == 'mixed':
        raise ValueError(_MIXED_REDUCIBLE_MULTI_TERM_ERROR)
    raise ValueError(
        _UNSUPPORTED_REQUEST_ERROR.format(command_type=data.get('command_type'))
    )
