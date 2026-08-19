# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

For the pedagogical background behind the drills (the mental-arithmetic technique the worksheets are built around), see `memo.md` (Japanese).

## Features
*   **Diverse Problem Types**: Generate worksheets for integer arithmetic, complements, 100-square tables, multiplication tables, square numbers, mental arithmetic, exact fraction arithmetic, fraction comparison, number properties (even/odd, multiples, divisors, LCM, GCD), and fraction/decimal conversion (simplification, common denominators, fraction-to-decimal, decimal-to-fraction, division-as-fraction) through the LaTeX renderer.
*   **Customizable Generation**: Extensive command-line options allow users to specify paper size, number ranges, operators, problem counts, and output formats.
*   **Reusable answer ceilings**: The LaTeX `ope` command accepts `--result-max` for two-term, parenthesized, multi-term, and missing-value expressions; the grade-2 Web menu uses it for advanced addition and subtraction whose answer is at most 1,000.
*   **PDF Output**: All worksheets are generated as high-quality PDF files, ready for printing.
*   **Answer Options**: Include answers at the bottom of the page, merge answer files, or output raw problem data to CSV for further analysis.
*   **Automated Batch Generation**: The `factory.sh` script provides an automated way to generate a wide variety of pre-configured worksheets.
*   **Web UI frontend** (`frontend/web`): a lightweight, Japanese-only, static multi-page implementation (plain HTML/CSS(Sass)/JS, no React or i18n library) whose drill menu is a grade -> category -> menu-item hierarchy matching `docs/uiux/calculation_drill_menu_parameters_v1.md` (issue #98). Written/vertical-format (筆算) output is available as a per-preset "出題形式" (式/筆算) setting on 18 add/sub/mul/div presets, not a separate preset category (issue #134). Talks to the Flask backend. (A second frontend, `frontend/spa` — a React SPA with English/Japanese switching and grade/exam-prep presets — existed alongside it until it was removed in issue #233.)

## Installation
The CLI (`nuts_calc_tex.py`) needs Python 3 and a LaTeX environment (`lualatex` by default, or `pdflatex` via `NUTS_CALC_TEX_ENGINE=pdflatex`) — it has no pip dependencies of its own. The Web UI additionally needs Flask, Flask-Cors, Node.js, and npm.

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

3.  **Install Web dependencies when using the Web UI** (the CLI itself needs no pip packages):
    ```bash
    pip install flask flask-cors
    cd frontend/web && npm install && cd ../..
    ```

4.  **Install a LaTeX environment** (required for both the CLI and the Web UI): `nuts_calc_tex.py`, including fraction, written-calculation, and entrance-exam-prep worksheets, uses the Japanese-capable `lualatex` engine by default (requires the `lualatex` binary, the `texlive-luatex` package for `luaotfload`, and the `fonts-noto-cjk` package on Debian/Ubuntu). Set `NUTS_CALC_TEX_ENGINE=pdflatex` to compile with `pdflatex` instead (on Debian/Ubuntu, install the TeX Live base and extra packages; the repository already vendors `longdivision`).

    To deactivate the virtual environment when you are done:
    ```bash
    deactivate
    ```

## Usage

### Generating Worksheets with `nuts_calc_tex.py`
The `nuts_calc_tex.py` script (in `backend/`) is the core generator. You can run it directly with various options.

```bash
cd backend
python nuts_calc_tex.py <paper_size> <command> [options]
```

**Example: Generate 5 pages of A4 addition problems**
```bash
python nuts_calc_tex.py A4 ope -o add -p 5 --out-file addition_A4_5pages.pdf
```

**Example: Generate 100-square calculation table (A3 size)**
```bash
python nuts_calc_tex.py A3 100 --out-file 100_square_A3.pdf
```

**Example: Generate multiplication table (kuku) for '7' in random order (A4 landscape)**
```bash
python nuts_calc_tex.py a4l 99 -a 7 --shuffle --out-file kuku_7_random_A4L.pdf
```

For a full list of options, run:
```bash
python nuts_calc_tex.py -h
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

For a single `-o add` or `-o sub`, `--a-fraction-form` and `--b-fraction-form`
independently select `proper` or `mixed` (mixed-number, e.g. `1 2/5`) operand
forms, or randomized `mix`; answers `>= 1` render as mixed numbers too
(`improper` is not supported for `frac`):

```bash
python3 nuts_calc_tex.py A4 frac -o add --same-denominator \
  --a-fraction-form mixed --b-fraction-form mixed --out-file mixed-fractions.pdf
```

Grade 3-6 fraction cards appear by default, since the Web UI's default and only reachable renderer is `latex` (issue #186; `NUTS_CALC_RENDERER=reportlab` is no longer available -- the ReportLab renderer, `nuts_calc.py`, was removed entirely in issue #232). The
curriculum source used for their placement is preserved under `docs/reference/`.
The same renderer exposes the grades 4-6 entrance-exam-prep section, which uses
multi-term, mixed-operator, and parenthesized `ope` expressions.

It also provides a `compare` command for comparison worksheets. Use
`--comparison-pattern` to select `same-denominator`, `same-numerator`, or
`different-denominators` (fraction-vs-fraction only); use `--a-fraction-form`
and `--b-fraction-form` to independently select `proper`, `improper`,
`mixed`, or randomized `mix` forms. Use `--a-kind`/`--b-kind` to mix in
`int`/`decimal` operands alongside `fraction` (default: `fraction` only,
matching the original behavior).

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

Use `--result-max` to cap the final displayed answer for any `ope` expression
shape. The command retries complete expressions and fails explicitly if the
requested ranges cannot produce a result under the ceiling.

```bash
python3 nuts_calc_tex.py A4 ope -o add \
  --a-min 1 --a-max 999 --b-min 1 --b-max 999 \
  --result-max 1000 --out-file addition-up-to-1000.pdf
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

For `frac -o mul`/`div` and two-term `mixed -o mul`/`div` (with one `fraction`
and one `int` operand kind), use `--require-reducible`, `--no-reducible`, or
`--mixed-reducible` to require, forbid, or mix whether the raw (pre-
simplification) product/quotient needs reduction.

```bash
python3 nuts_calc_tex.py A4 frac -o mul --numerator-digits 1 --denominator-digits 1 \
  --proper-operands --require-reducible --out-file reducible-fractions.pdf
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
    *   By default (no env vars needed) the app generates PDFs via `nuts_calc_tex.py` with the Japanese-capable `lualatex` engine (issue #186); this requires the `lualatex` binary, the `texlive-luatex` package, and the `fonts-noto-cjk` package (see Dependencies below). `NUTS_CALC_RENDERER=reportlab` is no longer available -- the ReportLab renderer, `nuts_calc.py`, was removed entirely in issue #232.
    *   (Optional) Set `NUTS_CALC_TEX_ENGINE=pdflatex` to use the `pdflatex` engine instead of the default `lualatex`; this requires `pdflatex` to be installed (see Dependencies below). Example:
        ```bash
        NUTS_CALC_TEX_ENGINE=pdflatex python app.py
        ```

2.  **Start the frontend** (`frontend/web`, Japanese only, no React/i18n library):
    ```bash
    cd frontend/web
    npm install
    npm run dev
    ```
    Typically runs on `http://localhost:5173`.

Once running, open your browser to the frontend's address (e.g., `http://localhost:5173`) to access the web interface.

### Running checks

```bash
cd backend && python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py
node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js
cd frontend/web && npm run build
```

`backend/tests/test_nuts_calc_init.py` is excluded above because 9 expectations still pin the old `exit()` status while the implementation correctly uses `exit(1)`; see `docs/L2_development/test.md`. `frontend/web` has no lint script and no `npm test` script, but `frontend/web/src/drillPresets.test.js` (node:test) covers its own drill-menu data model directly (issue #98), and `frontend/web/src/presetDetail.test.js` covers `presetDetail.js`'s pure problem-count/summary-building/example-to-KaTeX helpers (issues #100, #132); `frontend/web/src/drillPresets.js` diverged from the former `frontend/spa`'s version in #98 and no longer copies it (`frontend/spa` itself was removed entirely in issue #233); its former `drillCatalog.js` adapter was removed in #110 once `catalog.js`/`preset.js` stopped depending on it.

## Dependencies
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   Node.js and npm (for `frontend/web`)
*   `lualatex`, `texlive-luatex`, and `fonts-noto-cjk` -- required for the Web UI's default renderer (`nuts_calc_tex.py` with the Japanese-capable `lualatex` engine, issue #186; see Architecture below)
*   (Optional) `pdflatex` -- an alternative LaTeX engine for `nuts_calc_tex.py`, selectable via `NUTS_CALC_TEX_ENGINE=pdflatex`; not needed with the default `lualatex` engine

## Architecture

The repository is organized as `backend/` + `frontend/{web}` (`backend`/`frontend` could still be split into separate repositories in the future if needed). It previously held two independent frontends, `frontend/{spa,web}`, until `frontend/spa` was removed in issue #233. There are three user-facing ways to generate a worksheet:

*   **CLI**: `backend/nuts_calc_tex.py` → LaTeX (`lualatex`/`pdflatex`) → PDF/CSV. No server, no database, no persisted state. The original ReportLab CLI, `nuts_calc.py`, was removed entirely in issue #232 (previously unreachable via the Web UI since issue #186).
*   **Web UI**: `frontend/web`, a lightweight static multi-page site, → Flask backend (`backend/app.py`) → `backend/renderers.py` → `subprocess` call to `nuts_calc_tex.py` (the only renderer since issue #232; the renderer-switching mechanism itself, via `NUTS_CALC_RENDERER`, is kept for a possible future renderer) → generated PDF is streamed back to the browser. The backend holds no drill-generation logic of its own; it only translates form input into CLI arguments. As of issue #199, `command_type: 'com'` is the one exception: `backend/app.py` calls `nuts_calc_tex.py`'s internal presentation API (`build_presentation_document_tex`, issue #183) directly instead of going through the `subprocess` path, for the first command group migrated under the staged `/generate-pdf` migration tracked in issue #174; every other command type is unaffected. The former `frontend/spa` was the only frontend with a UI path to `command_type: 'com'` (presets and a free-form generator form); `frontend/web` has none. `frontend/web` calls `POST /generate-pdf` and `GET /renderer-info`, and is an independent npm project (not sharing a package with `backend`), since a future repo split was anticipated; its `verticalLayout.js` still mirrors the former `frontend/spa`'s copy, but its `drillPresets.js` has its own grade -> category -> menu-item data model (issue #98) and no longer duplicates `frontend/spa`'s version. `frontend/web` additionally calls a third endpoint, `POST /generate-problems` (issue #138), to fetch live-generated example problems (JSON, no PDF) for its preset detail screen; `backend/problem_generation.py` serves it by calling the CLI's data-generation functions in-process instead of shelling out. See `docs/L3_implementation/api.md`.
*   **Batch**: `backend/factory.sh` is a third, batch-oriented entry point that calls `nuts_calc_tex.py` repeatedly to populate a `dist/` directory with a fixed set of worksheets.

`nuts_calc_tex.py` implements twenty commands: seven with 1:1 semantics to the removed `nuts_calc.py`, the LaTeX-only `frac`, `mixed`, and `compare` commands, the LaTeX-only `evenodd`, `multiples`, and `divisors` number-property commands, the LaTeX-only `lcm` and `gcd` pair-number commands, and the LaTeX-only `simplify`, `commondenom`, `frac2dec`, `dec2frac`, and `divfrac` fraction/decimal conversion commands. It also owns decimal, written-calculation, and carry-aware drill behavior. Its LaTeX compilation step is pluggable via a `LatexEngineAdapter` (`NUTS_CALC_TEX_ENGINE`, default `lualatex` as of issue #186); the Japanese-capable `lualatex` adapter is the default (see Installation above), and `pdflatex` remains available via `NUTS_CALC_TEX_ENGINE=pdflatex`, though existing English-label workarounds for `pdflatex`'s lack of CJK font support are unchanged by either engine. See `docs/L3_implementation/backend/nuts_calc_tex.py.md`.

See `docs/L1_project/project_overview.md` and `docs/L0_concept/concept.md` for the full breakdown and file/line references.

## Design Principles

*   **Renderer-owned drill logic.** The web backend does not implement worksheet generation; it translates requests and shells out to the selected renderer. Most CLI parameters are shared; LaTeX-only features such as `frac` are always available now that `latex` is the Web UI's default and only reachable renderer (issue #186).
*   **No dependency pinning on the Python side.** There is no lock file, `requirements.txt`, or `pyproject.toml`; dependencies are installed ad hoc. This reflects the project's scope as a small personal/batch-generation tool rather than a deployed service.
*   **Local tests are the current quality gate (no CI yet).** pytest covers both generators and backend translation; Node's built-in test runner covers `frontend/web`'s own `drillPresets.test.js` (issue #98). Renderer-dependent tests compile PDF/CSV output when dependencies are available.
*   **One frontend, no shared package.** `frontend/web` was added as a lightweight (no React, no i18n library, Japanese-only) alternative to the former `frontend/spa` (removed in issue #233), built as a genuine static multi-page site rather than a single-page JS router. It is an independent npm project; its `verticalLayout.js` still duplicates the former `frontend/spa`'s copy, but its drill-menu data model (`drillPresets.js`) diverged from `frontend/spa`'s in issue #98 to match `docs/uiux/calculation_drill_menu_parameters_v1.md` exactly. It does not depend on a shared internal package, anticipating a possible future split of `backend`/`frontend` into separate repositories.

## License
MIT License
