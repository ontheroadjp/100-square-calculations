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
    """
    target = data.get('a_value')
    if target is None:
        raise ValueError("a_value (complement target) is required for the 'com' command.")
    if target < nuts_calc_tex.MIN_COMPLEMENT_TARGET:
        raise ValueError(
            f"a_value (complement target) must be at least {nuts_calc_tex.MIN_COMPLEMENT_TARGET} "
            "for the 'com' command."
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
        # nuts_calc.py/nuts_calc_tex.py print validation failure reasons to
        # stdout (not stderr), so stdout must take priority here.
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
