from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os

import problem_generation
import renderer_config
import three_layer_renderer

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# Directory to store generated PDFs temporarily
PDF_OUTPUT_DIR = './generated_pdfs'
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not data.get('paper_size') or not data.get('command_type'):
        return jsonify({'error': 'Missing required parameters: paper_size or command_type'}), 400

    try:
        output_filepath, output_filename = three_layer_renderer.render_worksheet_pdf(
            data, PDF_OUTPUT_DIR
        )

        # Return the generated PDF
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)

    except ValueError as e:
        app.logger.error(f"Invalid renderer configuration or request: {e}")
        return jsonify({'error': str(e)}), 500
    except RuntimeError as e:
        # Raised by three_layer_renderer's builders when engine_adapter.compile()
        # fails (see three_layer_renderer.py for why this can't be a normal exception).
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
        renderer_name = renderer_config.get_renderer_name()
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
        return jsonify({'renderer': renderer_config.get_renderer_name()})
    except ValueError as e:
        app.logger.error(f"Invalid renderer configuration: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
