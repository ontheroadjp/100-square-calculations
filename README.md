# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

## Features
*   **Diverse Problem Types**: Generate worksheets for basic arithmetic operations (addition, subtraction, multiplication, division), complements, 100-square calculation tables, multiplication tables (kuku), square numbers, and specific mental arithmetic problems.
*   **Customizable Generation**: Extensive command-line options allow users to specify paper size, number ranges, operators, problem counts, and output formats.
*   **PDF Output**: All worksheets are generated as high-quality PDF files, ready for printing.
*   **Answer Options**: Include answers at the bottom of the page, merge answer files, or output raw problem data to CSV for further analysis.
*   **Automated Batch Generation**: The `factory.sh` script provides an automated way to generate a wide variety of pre-configured worksheets.

## Installation
To use this generator, you need Python 3. It is highly recommended to use a virtual environment to manage dependencies. A LaTeX environment is optional, primarily if you plan to use other LaTeX-based tools or older versions of this project that might have relied on it.

> **Note:** there is no `requirements.txt`/`pyproject.toml`/`setup.py` in this repo, so dependencies must be installed manually — see step 3 and the Dependencies section below.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ontheroadjp/100-square-calculations.git
    cd 100-square-calculations
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the CLI dependency**:
    ```bash
    pip install reportlab
    ```

4.  **(Optional) Install LaTeX environment**: While `nuts_calc.py` uses ReportLab for PDF generation, if you encounter issues or plan to use other LaTeX-based tools, ensure you have a LaTeX distribution (e.g., TeX Live, MiKTeX) with `platex` and `dvipdfmx` installed.

    To deactivate the virtual environment when you are done:
    ```bash
    deactivate
    ```

## Usage

### Generating Worksheets with `nuts_calc.py`
The `nuts_calc.py` script is the core generator. You can run it directly with various options.

```bash
python nuts_calc.py <paper_size> <command> [options]
```

**Example: Generate 5 pages of A4 addition problems**
```bash
python nuts_calc.py A4 ope -o add -p 5 --out-file addition_A4_5pages.pdf
```

**Example: Generate 100-square calculation table (A3 size)**
```bash
python nuts_calc.py A3 100 --out-file 100_square_A3.pdf
```

**Example: Generate multiplication table (kuku) for '7' in random order (A4 landscape)**
```bash
python nuts_calc.py a4l 99 -a 7 --shuffle --out-file kuku_7_random_A4L.pdf
```

For a full list of options, run:
```bash
python nuts_calc.py -h
```

### Batch Generation with `factory.sh`
The `factory.sh` script automates the generation of a predefined set of worksheets, creating a structured output directory (`dist/`).

```bash
./factory.sh
```

This will generate a variety of mental arithmetic and other practice sheets into the `dist/` directory. Review the `factory.sh` script to understand the specific types and configurations of worksheets it generates.

### Running the Web Interface (React + Flask)

To use the web interface, you need to start both the Flask backend and the React frontend.

1.  **Start the Flask Backend**:
    *   Open a terminal and navigate to the `web/backend` directory:
        ```bash
        cd web/backend
        ```
    *   Ensure your virtual environment is activated (if you followed the setup):
        ```bash
        source ../../venv/bin/activate # Adjust path if your venv is elsewhere
        ```
    *   Run the Flask app:
        ```bash
        python app.py
        ```
    *   The backend will typically run on `http://127.0.0.1:5000`.

2.  **Start the React Frontend**:
    *   Open a *new terminal window* and navigate to the `web/frontend` directory:
        ```bash
        cd web/frontend
        ```
    *   Start the React development server:
        ```bash
        npm run dev
        ```
    *   The frontend will typically run on `http://localhost:5173`.

Once both are running, open your browser to the frontend's address (e.g., `http://localhost:5173`) to access the web interface.

## Dependencies
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   Node.js and npm (for React frontend)
*   (Optional) LaTeX environment (for `platex`, `dvipdfmx` if used by other tools or older versions)

## License
MIT License