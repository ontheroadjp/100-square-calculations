from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import contextlib
import io
import math
import shutil
import subprocess
import os
import uuid

import nuts_calc_tex
import problem_generation
import renderers

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# Directory to store generated PDFs temporarily
PDF_OUTPUT_DIR = './generated_pdfs'
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


def _generate_com_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'com' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183) instead of shelling
    out through renderers.py's subprocess path (issue #199, the first
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

    problems = nuts_calc_tex.generate_com_problems(target, rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_com_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _is_plain_mixed_pdf_request(data: renderers.RendererRequest) -> bool:
    """Return whether data selects the basic two-term mixed worksheet."""
    if data.get('command_type') != 'mixed':
        return False
    if data.get('mixed_operators') or data.get('reducible_mode') is not None:
        return False
    return not any(key in data for key in ('terms', 'terms_min', 'terms_max'))


def _generate_mixed_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """Build a basic two-term mixed PDF through the presentation API.

    Operand kinds, operator, fraction digit counts, and decimal places retain
    the CLI defaults when omitted. Multi-term, mixed-operator, and reducibility
    variants remain on the subprocess path and are excluded by the caller.
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

    terms_min, terms_max = nuts_calc_tex.resolve_term_range(
        nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT,
        nuts_calc_tex.TERM_COUNT_FLOOR_DEFAULT,
        False,
    )
    problems = nuts_calc_tex.generate_mixed_problems(
        a_kinds, b_kinds, operators, False,
        numerator_digits, denominator_digits, decimal_places,
        terms_min, terms_max, rows * columns, 1,
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_mixed_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_lcm_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_number_pair_problems(math.lcm, nums_a, nums_b, rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_lcm_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_divfrac_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_divfrac_problems(
        nums_a, nums_b, rows * columns, 1
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_divfrac_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_gcd_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_number_pair_problems(math.gcd, nums_a, nums_b, rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_gcd_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_evenodd_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_evenodd_problems(nums_a, rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_evenodd_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_kuku_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a '99' (times-table / kuku) command PDF via nuts_calc_tex.py's
    internal presentation API (build_presentation_document_tex, issue #183),
    mirroring _generate_com_pdf's pattern (issue #199) for this pattern-1a
    migration (#208). Basic-case only: a_value plus optional rows/columns/
    descend/shuffle, always a single blank (practice) page, non-reverse order
    (reverse/with_bottom_answer/with_name_field/multi-page/merge are not
    wired here, matching _generate_com_pdf's scope). descend/shuffle are
    supported (unlike the other omitted flags) because frontend/web's
    g2-kuku preset (drillPresets.js) sends them for its descending/random
    question-order settings; silently ignoring them here would regress that
    live feature once this command_type stops reaching renderers.py's
    subprocess path.

    '99' reads a_value directly like 'com' (it's always a literal value
    there, never a digit count -- issue #230); see
    problem_generation.validate_kuku_a_value's docstring for the shared
    validation this reuses.
    """
    a_value = problem_generation.validate_kuku_a_value(data.get('a_value'))
    descend = bool(data.get('descend', False))
    shuffle = bool(data.get('shuffle', False))

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

    problems = nuts_calc_tex.generate_kuku_problems(a_value, rows * columns, 1, descend, shuffle)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_kuku_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_abc_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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

    problems = nuts_calc_tex.generate_abc_problems(rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_abc_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_pi_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'pi' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), mirroring
    _generate_com_pdf's pattern (issue #199) for the pattern-1a
    `99`/`squ`/`pi`/`lcm`/`gcd` migration group (issue #210). Basic-case
    only: a_value plus optional rows/columns/descend/shuffle, always a
    single blank (practice) page -- with_bottom_answer/with_name_field/
    multi-page/merge/reverse are not wired for 'pi' yet (explicitly out of
    scope for #210, matching _generate_com_pdf's scope).

    'pi' reads a_value directly (like 'com', not a digit-count shorthand --
    see _generate_com_pdf's docstring).
    """
    start_num = problem_generation.validate_pi_start(data.get('a_value'))
    descend = bool(data.get('descend', False))
    shuffle = bool(data.get('shuffle', False))

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

    problems = nuts_calc_tex.generate_pi_problems(start_num, rows * columns, 1, descend, shuffle)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_pi_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _is_plain_ope_pdf_request(data: renderers.RendererRequest) -> bool:
    """
    True when `data` requests the plain 2-term `ope` PDF this issue (#205,
    the first migration under the pattern-1a tracking issue #201) covers:
    the horizontal add/sub/mul/div/mix layout (build_horizontal_block_tex),
    with none of the flags that select a different content-format pattern
    or a different pattern-1a variant migrated separately --
    vertical(pattern 6)/intermediate(pattern 5)/use_parentheses(#206's tree
    variant, migrated by _is_tree_ope_pdf_request)/missing_value(pattern 2)/
    the terms family (terms/terms_min/terms_max/mixed_operators, #207's
    flat multi-term variant, migrated by _is_multi_term_ope_pdf_request).
    Every other combination keeps using renderers.py's subprocess path.
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


def _generate_ope_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_ope_problems(
        nums_a, nums_b, operator, rows * columns, 1,
        a_decimal_places, b_decimal_places,
        data.get('carry_mode'), data.get('remainder_mode'), data.get('result_max'),
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _is_tree_ope_pdf_request(data: renderers.RendererRequest) -> bool:
    """
    True when `data` requests the `ope --use-parentheses` ('tree' variant)
    PDF this issue (#206, following #205's plain 2-term migration under the
    pattern-1a tracking issue #201) covers: command_type == 'ope' with
    use_parentheses set, and none of vertical/intermediate/missing_value
    also set -- each is mutually exclusive with --use-parentheses per
    nuts_calc_tex.py's _init() validation (nuts_calc_tex.py:676-692), so a
    request combining them keeps using the subprocess path unchanged. The
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


def _generate_tree_ope_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build an `ope --use-parentheses` (tree variant) command PDF via
    nuts_calc_tex.py's internal presentation API
    (build_presentation_document_tex, issue #183), mirroring
    _generate_ope_pdf's pattern (issue #205) for the pattern-1a tree-variant
    migration (#201/#206). Basic-case only: a/b range (a_digits/b_digits or
    a_min/a_max/b_min/b_max), operator, mixed_operators, the terms family
    (terms/terms_min/terms_max), result_max, plus rows/columns -- always a
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
    problems = nuts_calc_tex.generate_tree_ope_problems(
        nums_a, nums_b, operator, mixed_operators, terms_min, terms_max,
        rows * columns, 1, data.get('result_max'),
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_tree_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _is_multi_term_ope_pdf_request(data: renderers.RendererRequest) -> bool:
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


def _generate_multi_term_ope_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_multi_term_ope_problems(
        nums_a, nums_b, operator, mixed_operators, terms_min, terms_max,
        rows * columns, 1, data.get('result_max'),
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_multi_term_ope_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_squ_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
    """
    Build a 'squ' command PDF via nuts_calc_tex.py's internal presentation
    API (build_presentation_document_tex, issue #183), following #199's
    'com' precedent (issue #209, tracked under #174/B-5's remaining
    pattern-1a migrations #208/#209/#210/#211/#212). Basic-case only:
    a_value plus optional rows/columns, always a single blank (practice)
    page -- descend/shuffle/reverse/with_bottom_answer/with_name_field/
    multi-page/merge are not wired for 'squ' yet (explicitly out of scope
    for #209, matching #199's scope).

    'squ' reads a_value directly (it's always a literal starting square
    number, never a digit count -- like 'com', unlike
    nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS).
    """
    start_num = problem_generation.validate_squ_start(data.get('a_value'))

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

    problems = nuts_calc_tex.generate_squ_problems(start_num, rows * columns, 1, False, False)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_squ_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_multiples_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_multiples_problems(
        nums_a, rows * columns, 1, multiples_count
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_multiples_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_divisors_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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
    problems = nuts_calc_tex.generate_divisors_problems(nums_a, rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_divisors_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_frac_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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

    problems = nuts_calc_tex.generate_fraction_problems(
        numerator_digits,
        denominator_digits,
        operators,
        rows * columns,
        1,
        same_denominator,
        proper_operands,
        proper_result,
        different_denominators,
        a_fraction_form,
        b_fraction_form,
        reducible_mode,
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_fraction_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_simplify_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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

    problems = nuts_calc_tex.generate_simplify_problems(
        numerator_digits, denominator_digits, rows * columns, 1
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_simplify_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_frac2dec_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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

    problems = nuts_calc_tex.generate_frac2dec_problems(
        numerator_digits, denominator_digits, rows * columns, 1
    )
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_frac2dec_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


def _generate_dec2frac_pdf(data: renderers.RendererRequest, output_dir: str) -> tuple[str, str]:
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

    problems = nuts_calc_tex.generate_dec2frac_problems(rows * columns, 1)
    page = nuts_calc_tex.PresentationPage(
        problems=problems, indices=[problem.index for problem in problems]
    )
    tex_source = nuts_calc_tex.build_presentation_document_tex(
        data['paper_size'],
        pages=[page],
        content_format=nuts_calc_tex.build_dec2frac_slot_content_tex,
        page_shell=nuts_calc_tex.DEFAULT_PAGE_SHELL,
        content_area_layout=nuts_calc_tex.ContentAreaLayout(rows=rows, columns=columns),
        engine_adapter=engine_adapter,
        show_answer=False,
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


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not data.get('paper_size') or not data.get('command_type'):
        return jsonify({'error': 'Missing required parameters: paper_size or command_type'}), 400

    try:
        if data.get('command_type') == 'com':
            output_filepath, output_filename = _generate_com_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'lcm':
            output_filepath, output_filename = _generate_lcm_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'divfrac':
            output_filepath, output_filename = _generate_divfrac_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'gcd':
            output_filepath, output_filename = _generate_gcd_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'evenodd':
            output_filepath, output_filename = _generate_evenodd_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == '99':
            output_filepath, output_filename = _generate_kuku_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'aBc':
            output_filepath, output_filename = _generate_abc_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'pi':
            output_filepath, output_filename = _generate_pi_pdf(data, PDF_OUTPUT_DIR)
        elif _is_plain_mixed_pdf_request(data):
            output_filepath, output_filename = _generate_mixed_pdf(data, PDF_OUTPUT_DIR)
        elif _is_plain_ope_pdf_request(data):
            output_filepath, output_filename = _generate_ope_pdf(data, PDF_OUTPUT_DIR)
        elif _is_tree_ope_pdf_request(data):
            output_filepath, output_filename = _generate_tree_ope_pdf(data, PDF_OUTPUT_DIR)
        elif _is_multi_term_ope_pdf_request(data):
            output_filepath, output_filename = _generate_multi_term_ope_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'squ':
            output_filepath, output_filename = _generate_squ_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'multiples':
            output_filepath, output_filename = _generate_multiples_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'divisors':
            output_filepath, output_filename = _generate_divisors_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'frac':
            output_filepath, output_filename = _generate_frac_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'simplify':
            output_filepath, output_filename = _generate_simplify_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'frac2dec':
            output_filepath, output_filename = _generate_frac2dec_pdf(data, PDF_OUTPUT_DIR)
        elif data.get('command_type') == 'dec2frac':
            output_filepath, output_filename = _generate_dec2frac_pdf(data, PDF_OUTPUT_DIR)
        else:
            renderer_name = renderers.get_renderer_name()
            output_filepath, output_filename, result = renderers.run(
                data, PDF_OUTPUT_DIR, renderer_name
            )
            app.logger.info(f"{renderer_name} stdout: {result.stdout}")
            if result.stderr:
                app.logger.warning(f"{renderer_name} stderr: {result.stderr}")

        # Return the generated PDF
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)

    except ValueError as e:
        app.logger.error(f"Invalid renderer configuration or request: {e}")
        return jsonify({'error': str(e)}), 500
    except subprocess.CalledProcessError as e:
        # nuts_calc_tex.py prints validation failure reasons to stdout (not
        # stderr), so stdout must take priority here.
        error_reason = e.stdout or e.stderr
        app.logger.error(f"Error running renderer: stdout={e.stdout!r} stderr={e.stderr!r}")
        return jsonify({'error': f'PDF generation failed: {error_reason}'}), 500
    except RuntimeError as e:
        # Raised by _generate_com_pdf when engine_adapter.compile() fails
        # (see its docstring for why this can't be a normal exception).
        app.logger.error(f"Error compiling PDF via presentation API: {e}")
        return jsonify({'error': str(e)}), 500
    except FileNotFoundError:
        app.logger.error("Renderer script not found. Is the script in the correct path?")
        return jsonify({'error': 'Renderer script not found. Please ensure the script is in the correct path.'}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/generate-problems', methods=['POST'])
def generate_problems():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not data.get('paper_size') or not data.get('command_type'):
        return jsonify({'error': 'Missing required parameters: paper_size or command_type'}), 400

    num = data.get('num')
    if not isinstance(num, int) or isinstance(num, bool) or num < 1:
        return jsonify({'error': 'Missing or invalid required parameter: num (must be a positive integer)'}), 400

    try:
        renderer_name = renderers.get_renderer_name()
        if data.get('command_type') == '100':
            # `100` (hundred-square addition table) uses a dedicated
            # `{"table": {...}}` response envelope, not `{"problems": [...]}`:
            # a single 10x10 grid has no `num`-many problem decomposition
            # (issue #228, reversing #169's exclusion). `num` stays required
            # by the guard above for uniform validation, but is ignored here.
            table = problem_generation.generate_hundred_square_table(data)
            return jsonify(table)
        problems = problem_generation.generate_problems(data, renderer_name)
        return jsonify({'problems': problems})

    except ValueError as e:
        app.logger.error(f"Invalid problem-generation request: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/renderer-info', methods=['GET'])
def renderer_info():
    try:
        return jsonify({'renderer': renderers.get_renderer_name()})
    except ValueError as e:
        app.logger.error(f"Invalid renderer configuration: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
