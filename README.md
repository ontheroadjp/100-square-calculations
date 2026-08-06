# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

For the pedagogical background behind the drills (the mental-arithmetic technique the worksheets are built around), see `memo.md` (Japanese).

## Features
*   **Diverse Problem Types**: Generate worksheets for integer arithmetic, complements, 100-square tables, multiplication tables, square numbers, mental arithmetic, and exact fraction arithmetic through the LaTeX renderer.
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

4.  **(Optional) Install a LaTeX environment**: `nuts_calc_tex.py`, including fraction worksheets and written-calculation output, requires `pdflatex`. On Debian/Ubuntu, install the TeX Live base and extra packages; the repository already vendors `longdivision`.

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

### Fraction worksheets with `nuts_calc_tex.py`

The LaTeX renderer adds a `frac` command with exact, reduced answers and
constraints for numerator/denominator digit counts and denominator matching.

```bash
python3 nuts_calc_tex.py A4 frac \
  --numerator-digits 1 --denominator-digits 1 \
  --same-denominator --proper-operands --proper-result \
  -o add sub --out-file fractions.pdf
```

Grade 3-6 fraction cards appear only with `NUTS_CALC_RENDERER=latex`. The
curriculum source used for their placement is preserved under `docs/reference/`.

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
    *   (Optional) Set `NUTS_CALC_RENDERER=latex` before starting the app to generate PDFs via `nuts_calc_tex.py` instead of the default `nuts_calc.py` (`reportlab`); this requires `pdflatex` to be installed (see Dependencies below).

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
*   (Optional) `pdflatex` -- required only for `nuts_calc_tex.py`, an experimental, fully independent LaTeX-rendered prototype (see Architecture below)

## Architecture

There are two independent ways to generate a worksheet, both ultimately driven by the same CLI:

*   **CLI**: `nuts_calc.py` → ReportLab → PDF/CSV. No server, no database, no persisted state.
*   **Web UI**: React frontend (`web/frontend`) → Flask backend (`web/backend/app.py`) → `web/backend/renderers.py` → `subprocess` call to `nuts_calc.py` (default) or `nuts_calc_tex.py` (via `NUTS_CALC_RENDERER=latex`) → generated PDF is streamed back to the browser. The backend holds no drill-generation logic of its own; it only translates form input into CLI arguments shared by both renderers.

`factory.sh` is a third, batch-oriented entry point that calls `nuts_calc.py` repeatedly to populate a `dist/` directory with a fixed set of worksheets.

**Experimental**: `nuts_calc_tex.py` is independent from ReportLab and implements eight commands: the seven commands planned by issue #19 plus the LaTeX-only `frac` command. Fraction answers use exact rational arithmetic, and Web fraction cards are renderer-gated because `nuts_calc.py` does not implement `frac`. See `docs/L3_implementation/nuts_calc_tex.py.md`.

See `docs/L1_project/project_overview.md` and `docs/L0_concept/concept.md` for the full breakdown and file/line references.

## Design Principles

*   **Renderer-owned drill logic.** The web backend does not implement worksheet generation; it translates requests and shells out to the selected renderer. Most CLI parameters are shared, while LaTeX-only features such as `frac` are hidden when ReportLab is active.
*   **No dependency pinning on the Python side.** There is no lock file, `requirements.txt`, or `pyproject.toml`; dependencies are installed ad hoc. This reflects the project's scope as a small personal/batch-generation tool rather than a deployed service.
*   **The Python generators and Web backend have pytest coverage (no CI yet).** Unit tests cover problem generation and backend command translation; end-to-end tests compile PDF/CSV output when renderer dependencies are available. Run with `pip install pytest && python3 -m pytest` after installing the Python dependencies.

## License
MIT License
