# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

For the pedagogical background behind the drills (the mental-arithmetic technique the worksheets are built around), see `memo.md` (Japanese).

## Features
*   **Diverse Problem Types**: Generate worksheets for integer arithmetic, complements, 100-square tables, multiplication tables, square numbers, mental arithmetic, exact fraction arithmetic, fraction comparison, number properties (even/odd, multiples, divisors, LCM, GCD), and fraction/decimal conversion (simplification, common denominators, fraction-to-decimal, decimal-to-fraction, division-as-fraction) through the LaTeX renderer.
*   **Customizable Generation**: Extensive command-line options allow users to specify paper size, number ranges, operators, problem counts, and output formats.
*   **PDF Output**: All worksheets are generated as high-quality PDF files, ready for printing.
*   **Answer Options**: Include answers at the bottom of the page, merge answer files, or output raw problem data to CSV for further analysis.
*   **Automated Batch Generation**: The `factory.sh` script provides an automated way to generate a wide variety of pre-configured worksheets.
*   **Grade and exam-prep presets**: The Web UI groups drills by grades 1-6. With the LaTeX renderer, grade 1 has six addition/subtraction cards split by carrying/borrowing conditions, and grades 4-6 add 27 entrance-exam-prep presets (three stages and three levels per grade).
*   **Two independent Web UI frontends**: `frontend/spa` is a React SPA with English/Japanese language switching. `frontend/web` is a lightweight, Japanese-only, static multi-page implementation (plain HTML/CSS(Sass)/JS, no React or i18n library) offering the same drill-catalog and custom-generation features. Both talk to the same Flask backend.

## Installation
To use the ReportLab generator, you need Python 3. The Web UI additionally needs Flask, Flask-Cors, Node.js, and npm. A LaTeX environment with `pdflatex` is required when using `nuts_calc_tex.py` or `NUTS_CALC_RENDERER=latex`.

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

4.  **Install Web dependencies when using the Web UI**:
    ```bash
    pip install flask flask-cors
    cd frontend/spa && npm install && cd ../..   # React SPA
    cd frontend/web && npm install && cd ../..   # lightweight static UI (optional, only one is needed)
    ```

5.  **(Optional) Install a LaTeX environment**: `nuts_calc_tex.py`, including fraction, written-calculation, and entrance-exam-prep worksheets, requires `pdflatex`. On Debian/Ubuntu, install the TeX Live base and extra packages; the repository already vendors `longdivision`.

    To deactivate the virtual environment when you are done:
    ```bash
    deactivate
    ```

## Usage

### Generating Worksheets with `nuts_calc.py`
The `nuts_calc.py` script (in `backend/`) is the core generator. You can run it directly with various options.

```bash
cd backend
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
The examples below assume you are in the `backend/` directory (`cd backend`).

```bash
python3 nuts_calc_tex.py A4 frac \
  --numerator-digits 1 --denominator-digits 1 \
  --same-denominator --proper-operands --proper-result \
  -o add sub --out-file fractions.pdf
```

Grade 3-6 fraction cards appear only with `NUTS_CALC_RENDERER=latex`. The
curriculum source used for their placement is preserved under `docs/reference/`.
The same renderer exposes the grades 4-6 entrance-exam-prep section, which uses
multi-term, mixed-operator, and parenthesized `ope` expressions.

It also provides a `compare` command for fraction comparison worksheets. Use
`--comparison-pattern` to select `same-denominator`, `same-numerator`, or
`different-denominators`; use `--a-fraction-form` and `--b-fraction-form` to
independently select `proper`, `improper`, `mixed`, or randomized `mix` forms.

```sh
python3 nuts_calc_tex.py A4 compare --comparison-pattern same-denominator \
  --a-fraction-form proper --b-fraction-form proper --out-file compare.pdf
```

It also provides decimal `ope`, the `mixed` integer/decimal/fraction command,
and carry-aware two-term integer addition/subtraction. Carry-required addition
and borrow-required subtraction sample within the configured operand ranges
(falling back to a digit-width-preserving synthesized pair if no matching
combination turns up); the one exception is borrow-required subtraction with
both ranges single-digit (1-9), where no positive-result borrow is possible,
so it falls back to the original 10-19-minus-one-digit sampling instead.

```bash
python3 nuts_calc_tex.py A4 ope -o add --carry-borrow --out-file carrying.pdf
python3 nuts_calc_tex.py A4 ope -o add sub --mixed-carry-borrow --out-file mixed-carry.pdf
```

For `ope -o div`, use `--remainder`, `--no-remainder`, or `--mixed-remainder` to
require, forbid, or mix a nonzero division remainder (the default, and
`--no-remainder`, behave the same as before this flag existed). Since plain
`pdflatex` has no CJK font support, a nonzero remainder is rendered with the
plain-math `\cdots` ellipsis shorthand (e.g. `11 ÷ 4 = 2 ⋯ 3`) rather than the
Japanese "あまり" label.

```bash
python3 nuts_calc_tex.py A4 ope -o div --remainder --out-file division-remainder.pdf
```

Use `--with-name-field` to print a `Name: ___` line in the page header (a
common setting shared across all twenty commands, not just `ope`). Since plain
`pdflatex` has no CJK font support, the label is rendered as English `Name:`
rather than the Japanese `なまえ：`, matching the existing `Date:`/`Time:`
labels.

```bash
python3 nuts_calc_tex.py A4 ope --with-name-field --out-file with-name.pdf
```

It also provides `lcm` and `gcd` commands for least-common-multiple and
greatest-common-divisor drills. Each problem draws two random integers and
hides only the answer (e.g. `LCM(a, b) = ___`); the English `LCM`/`GCD`
labels are used for the same CJK/pdflatex reason as `--with-name-field` above.

```bash
python3 nuts_calc_tex.py A4 lcm --out-file lcm.pdf
python3 nuts_calc_tex.py A4 gcd --out-file gcd.pdf
```

It also provides five fraction/decimal conversion commands: `simplify`
(reduce a fraction), `commondenom` (convert two fractions to a shared
denominator), `frac2dec` (convert a fraction to its exact terminating
decimal), `dec2frac` (convert a decimal to its reduced fraction), and
`divfrac` (express a division as an unreduced fraction, `a÷b = a/b`).
`simplify`/`commondenom`/`frac2dec` reuse the `--numerator-digits`/
`--denominator-digits` options shown above for `frac`.

```bash
python3 nuts_calc_tex.py A4 simplify --out-file simplify.pdf
python3 nuts_calc_tex.py A4 commondenom --out-file commondenom.pdf
python3 nuts_calc_tex.py A4 frac2dec --out-file frac2dec.pdf
python3 nuts_calc_tex.py A4 dec2frac --out-file dec2frac.pdf
python3 nuts_calc_tex.py A4 divfrac --out-file divfrac.pdf
```

### Batch Generation with `factory.sh`
The `factory.sh` script (in `backend/`) automates the generation of a predefined set of worksheets, creating a structured output directory (`dist/`).

```bash
cd backend
./factory.sh
```

This will generate a variety of mental arithmetic and other practice sheets into the `dist/` directory. Review the `factory.sh` script to understand the specific types and configurations of worksheets it generates.

### Running the Web Interface (Flask + one of the two frontends)

To use either web interface, you need to start the Flask backend and one of the two independent frontends. Both frontends talk to the same backend, so you only need to start one of them.

1.  **Start the Flask Backend**:
    *   Open a terminal and navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    *   Ensure your virtual environment is activated (if you followed the setup):
        ```bash
        source ../venv/bin/activate # Adjust path if your venv is elsewhere
        ```
    *   Run the Flask app:
        ```bash
        python app.py
        ```
    *   The backend will typically run on `http://127.0.0.1:5000`.
    *   (Optional) Set `NUTS_CALC_RENDERER=latex` before starting the app to generate PDFs via `nuts_calc_tex.py` instead of the default `nuts_calc.py` (`reportlab`); this requires `pdflatex` to be installed (see Dependencies below).

2.  **Start a frontend** — pick one:
    *   **React SPA** (`frontend/spa`, English/Japanese):
        ```bash
        cd frontend/spa
        npm install
        npm run dev
        ```
        Typically runs on `http://localhost:5173`.
    *   **Lightweight static UI** (`frontend/web`, Japanese only, no React/i18n library):
        ```bash
        cd frontend/web
        npm install
        npm run dev
        ```
        Typically runs on `http://localhost:5173` as well (Vite picks the next free port, e.g. `5174`, if both dev servers are running at once).

Once both are running, open your browser to the frontend's address (e.g., `http://localhost:5173`) to access the web interface.

### Running checks

```bash
cd backend && python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py
node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js
cd frontend/spa && npm run build
cd frontend/web && npm run build
```

`backend/tests/test_nuts_calc_init.py` is excluded above because 9 expectations still pin the old `exit()` status while the implementation correctly uses `exit(1)`; see `docs/L2_development/test.md`. `npm run lint` is also available for `frontend/spa`, but currently reports one `no-irregular-whitespace` error at `frontend/spa/src/drillPresets.js:433`. `frontend/web` has no lint/test script; `frontend/spa`'s pure-function tests indirectly cover the data/logic modules that `frontend/web` copies from it.

## Dependencies
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   Node.js and npm (for either `frontend/spa` or `frontend/web`)
*   (Optional) `pdflatex` -- required for `nuts_calc_tex.py` and `NUTS_CALC_RENDERER=latex` (see Architecture below)

## Architecture

The repository is organized as `backend/` + `frontend/{spa,web}`, so the Flask backend can be shared by two independent frontends (and so `backend`/`frontend` could be split into separate repositories in the future if needed). There are three user-facing ways to generate a worksheet:

*   **CLI**: `backend/nuts_calc.py` → ReportLab → PDF/CSV. No server, no database, no persisted state.
*   **Web UI**: a frontend (`frontend/spa`, a React SPA, or `frontend/web`, a lightweight static multi-page site) → Flask backend (`backend/app.py`) → `backend/renderers.py` → `subprocess` call to `nuts_calc.py` (default) or `nuts_calc_tex.py` (via `NUTS_CALC_RENDERER=latex`) → generated PDF is streamed back to the browser. The backend holds no drill-generation logic of its own; it only translates form input into CLI arguments shared by both renderers. Both frontends call the same two endpoints (`POST /generate-pdf`, `GET /renderer-info`) and duplicate the same handful of pure data/logic modules (`drillPresets.js`/`drillCatalog.js`/`verticalLayout.js`) rather than sharing a package, since a future repo split was anticipated.
*   **Batch**: `backend/factory.sh` is a third, batch-oriented entry point that calls `nuts_calc.py` repeatedly to populate a `dist/` directory with a fixed set of worksheets.

**Experimental**: `nuts_calc_tex.py` is independent from ReportLab and implements twenty commands: the seven ReportLab-compatible commands, the LaTeX-only `frac`, `mixed`, and `compare` commands, the LaTeX-only `evenodd`, `multiples`, and `divisors` number-property commands, the LaTeX-only `lcm` and `gcd` pair-number commands, and the LaTeX-only `simplify`, `commondenom`, `frac2dec`, `dec2frac`, and `divfrac` fraction/decimal conversion commands. It also owns decimal, written-calculation, and carry-aware drill behavior. Web cards using these features are renderer-gated because `nuts_calc.py` does not implement them. See `docs/L3_implementation/backend/nuts_calc_tex.py.md`.

See `docs/L1_project/project_overview.md` and `docs/L0_concept/concept.md` for the full breakdown and file/line references.

## Design Principles

*   **Renderer-owned drill logic.** The web backend does not implement worksheet generation; it translates requests and shells out to the selected renderer. Most CLI parameters are shared, while LaTeX-only features such as `frac` are hidden when ReportLab is active.
*   **No dependency pinning on the Python side.** There is no lock file, `requirements.txt`, or `pyproject.toml`; dependencies are installed ad hoc. This reflects the project's scope as a small personal/batch-generation tool rather than a deployed service.
*   **Local tests are the current quality gate (no CI yet).** pytest covers both generators and backend translation; Node's built-in test runner covers `frontend/spa`'s preset/catalog/layout pure functions. Renderer-dependent tests compile PDF/CSV output when dependencies are available. `frontend/web` has no automated tests of its own; its copied pure-function modules are indirectly covered by `frontend/spa`'s tests.
*   **Two frontends, one contract, no shared package.** `frontend/web` was added as a lightweight (no React, no i18n library, Japanese-only) alternative to `frontend/spa`, built as a genuine static multi-page site rather than a single-page JS router. Both frontends are independent npm projects that duplicate a small set of pure-data modules rather than depending on a shared internal package, anticipating a possible future split of `backend`/`frontend` into separate repositories.

## License
MIT License
