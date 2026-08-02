# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

For the pedagogical background behind the drills (the mental-arithmetic technique the worksheets are built around), see `memo.md` (Japanese).

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
*   (Optional) `pdflatex` -- required only for `nuts_calc_tex.py`, an experimental, fully independent LaTeX-rendered prototype (see Architecture below)

## Architecture

There are two independent ways to generate a worksheet, both ultimately driven by the same CLI:

*   **CLI**: `nuts_calc.py` → ReportLab → PDF/CSV. No server, no database, no persisted state.
*   **Web UI**: React frontend (`web/frontend`) → Flask backend (`web/backend/app.py`) → `subprocess` call to `nuts_calc.py` → generated PDF is streamed back to the browser. The backend holds no drill-generation logic of its own; it only translates form input into `nuts_calc.py` CLI arguments.

`factory.sh` is a third, batch-oriented entry point that calls `nuts_calc.py` repeatedly to populate a `dist/` directory with a fixed set of worksheets.

**Experimental**: `nuts_calc_tex.py` is a separate, fully independent prototype that renders worksheets via LaTeX (`pdflatex`) instead of ReportLab, with zero code sharing with `nuts_calc.py`. It implements the common CLI/PDF foundation (Phase 1), the `ope` command -- four arithmetic operations plus `mix`, horizontal and `--vertical` (hissan, via `xlop`/`longdivision`) format, and `--intermediate` (Phase 2) --, the `com` command -- complement-to-target problems (`a + __ = target`), horizontal only (Phase 3) --, the `100` command -- a 100-square addition table (11x11 grid with a shaded header row/column, via `xcolor`) (Phase 4) --, and the `99` command -- times-table (kuku) problems tiled across `--rows`x`--columns`, with `--descend`/`--reverse`/`--shuffle` ordering options (Phase 5) --, and the `aBc` command -- mental-arithmetic digit-pair conversion problems (a random 4-digit sequence `abcd` converted to its value via the two digit-pairs `ab`/`cd`), tiled across `--rows`x`--columns` (Phase 6). The other two commands (`squ`/`pi`) are not yet implemented. See `docs/L3_implementation/nuts_calc_tex.py.md` and tracking issue #19.

See `docs/L1_project/project_overview.md` and `docs/L0_concept/concept.md` for the full breakdown and file/line references.

## Design Principles

*   **Single source of drill logic.** The web backend does not reimplement worksheet generation — it always shells out to `nuts_calc.py`, so the CLI and the web UI can never drift into producing different problems for the same parameters.
*   **No dependency pinning on the Python side.** There is no lock file, `requirements.txt`, or `pyproject.toml`; dependencies are installed ad hoc. This reflects the project's scope as a small personal/batch-generation tool rather than a deployed service.
*   **`nuts_calc.py` has an automated pytest regression suite (no CI yet).** Unit tests cover the problem-data generation functions and `_init()` argument validation; end-to-end tests run the CLI as a subprocess and check the generated PDF/CSV output. Run with `pip install pytest && pytest` after installing the CLI dependency. The web frontend/backend are not yet covered.

## License
MIT License