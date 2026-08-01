from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import uuid

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

    # Construct command for nuts_calc.py
    # Example: python ../../nuts_calc.py A4 ope -o add -p 1 --out-file output.pdf
    command = ['python', '../../nuts_calc.py']

    # Required arguments
    paper_size = data.get('paper_size')
    command_type = data.get('command_type')

    if not paper_size or not command_type:
        return jsonify({'error': 'Missing required parameters: paper_size or command_type'}), 400

    command.append(paper_size)
    command.append(command_type)

    # Optional arguments
    if 'a_value' in data: command.extend(['--a-value', str(data['a_value'])])
    if 'b_value' in data: command.extend(['--b-value', str(data['b_value'])])
    if 'a_min' in data: command.extend(['--a-min', str(data['a_min'])])
    if 'a_max' in data: command.extend(['--a-max', str(data['a_max'])])
    if 'b_min' in data: command.extend(['--b-min', str(data['b_min'])])
    if 'b_max' in data: command.extend(['--b-max', str(data['b_max'])])
    if 'operator' in data and data['operator']:
        command.extend(['--operator', *data['operator']])
    if data.get('descend'): command.append('--descend')
    if data.get('reverse'): command.append('--reverse')
    if data.get('shuffle'): command.append('--shuffle')
    if data.get('intermediate'): command.append('--intermediate')
    if data.get('vertical'): command.append('--vertical')
    if 'rows' in data: command.extend(['--rows', str(data['rows'])])
    if 'columns' in data: command.extend(['--columns', str(data['columns'])])
    if data.get('with_bottom_answer'): command.append('--with-bottom-answer')
    if 'page' in data: command.extend(['--page', str(data['page'])])
    if data.get('merge'): command.append('--merge')
    if data.get('csv'): command.append('--csv')
    if data.get('debug'): command.append('--debug')

    # Generate a unique filename for the PDF
    output_filename = f"worksheet_{uuid.uuid4()}.pdf"
    output_filepath = os.path.join(PDF_OUTPUT_DIR, output_filename)
    command.extend(['--out-file', output_filepath])

    try:
        # Execute nuts_calc.py
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        app.logger.info(f"nuts_calc.py stdout: {result.stdout}")
        if result.stderr:
            app.logger.warning(f"nuts_calc.py stderr: {result.stderr}")

        # Return the generated PDF
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)

    except subprocess.CalledProcessError as e:
        app.logger.error(f"Error running nuts_calc.py: {e.stderr}")
        return jsonify({'error': f'PDF generation failed: {e.stderr}'}), 500
    except FileNotFoundError:
        app.logger.error("nuts_calc.py not found. Is the script in the correct path?")
        return jsonify({'error': 'nuts_calc.py not found. Please ensure the script is in the correct path.'}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
