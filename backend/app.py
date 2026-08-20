from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import contextlib
import io
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


def _is_plain_ope_pdf_request(data: renderers.RendererRequest) -> bool:
    """
    True when `data` requests the plain 2-term `ope` PDF this issue (#205,
    the first migration under the pattern-1a tracking issue #201) covers:
    the horizontal add/sub/mul/div/mix layout (build_horizontal_block_tex),
    with none of the flags that select a different content-format pattern
    or a not-yet-migrated pattern-1a-adjacent variant --
    vertical(pattern 6)/intermediate(pattern 5)/use_parentheses(#206's tree
    variant)/missing_value(pattern 2)/the terms family
    (terms/terms_min/terms_max/mixed_operators, #207's multi-term variant).
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
        elif _is_plain_ope_pdf_request(data):
            output_filepath, output_filename = _generate_ope_pdf(data, PDF_OUTPUT_DIR)
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
