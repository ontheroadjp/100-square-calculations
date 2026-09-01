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

For `ope -o mul` with asymmetric decimal places (`--a-decimal-places` !=
`--b-decimal-places`), add `--mixed-decimal-operand-order` to randomly swap
which operand carries the decimal per problem, so one worksheet mixes
"decimal x integer" and "integer x decimal". Multiplication is commutative, so
the product is unchanged; the flag is rejected for any other command or
operator, or when the two decimal-place counts are equal.

```bash
python3 nuts_calc_tex.py A4 ope -o mul --a-digits 2 --b-digits 1 \
  --a-decimal-places 1 --mixed-decimal-operand-order --out-file mixed-decimal-order.pdf
```

For `ope -o div` with a decimal divisor (`--b-decimal-places` >= 1), use
`--integer-dividend`, `--decimal-dividend` (the default behavior), or
`--mixed-dividend` to make the dividend a whole number, a decimal, or a
per-problem mix of both. With `--integer-dividend` the dividend is a whole
number, the divisor stays a decimal, and the quotient is an exact integer
(e.g. `96 ÷ 2.4 = 40`); it is rejected for any other command or operator, an
integer divisor, or when combined with `--remainder`/`--use-parentheses`/
`--missing-value`/the `--terms` family/`--intermediate`.

```bash
python3 nuts_calc_tex.py A4 ope -o div --a-digits 2 --b-digits 2 \
  --a-decimal-places 0 --b-decimal-places 1 --integer-dividend --out-file integer-dividend.pdf
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

### Running the Web Interface (Flask + `frontend/web`)

To use the Web UI, start the Flask backend and the sole frontend, `frontend/web`.

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
cd backend && python3 -m pytest -q
node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js frontend/web/vite.config.test.js
cd frontend/web && npm run build
```

The backend suite needs `pytest` and `pytest-xdist` (`pip install pytest pytest-xdist`). `backend/pytest.ini` sets `addopts = -n auto`, so `python3 -m pytest` fans the tests out across all CPU cores automatically; pass `-n0` to force serial execution when debugging a single test.

`frontend/web` has no lint script and no `npm test` script, but the three explicitly invoked `node:test` files cover the drill-menu data model, preset-detail pure helpers, and Vite sourcemap configuration. The stale `backend/tests/test_nuts_calc_init.py` suite was removed with the former ReportLab CLI in issue #232; the current backend command runs the complete suite without an ignore exception.

## Dependencies
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   `pytest` and `pytest-xdist` (`pip install pytest pytest-xdist`) -- for the backend test suite; `pytest-xdist` backs the `-n auto` parallel run configured in `backend/pytest.ini`
*   Node.js and npm (for `frontend/web`)
*   `lualatex`, `texlive-luatex`, and `fonts-noto-cjk` -- required for the Web UI's default renderer (`nuts_calc_tex.py` with the Japanese-capable `lualatex` engine, issue #186; see Architecture below)
*   (Optional) `pdflatex` -- an alternative LaTeX engine for `nuts_calc_tex.py`, selectable via `NUTS_CALC_TEX_ENGINE=pdflatex`; not needed with the default `lualatex` engine

## Architecture

The repository is organized as `backend/` + `frontend/{web}` (`backend`/`frontend` could still be split into separate repositories in the future if needed). It previously held two independent frontends, `frontend/{spa,web}`, until `frontend/spa` was removed in issue #233. There are three user-facing ways to generate a worksheet:

*   **CLI**: `backend/nuts_calc_tex.py` → LaTeX (`lualatex`/`pdflatex`) → PDF/CSV. No server, no database, no persisted state. The original ReportLab CLI, `nuts_calc.py`, was removed entirely in issue #232 (previously unreachable via the Web UI since issue #186).
*   **Web UI**: `frontend/web`, a lightweight static multi-page site, calls the Flask backend (`backend/app.py`), which streams generated PDFs back to the browser. The staged `/generate-pdf` migration tracked in issue #174 now serves every command through `nuts_calc_tex.py`'s internal presentation API (`build_presentation_document_tex`, issue #183): all 20 `command_type`s — `com`, `lcm`, `divfrac`, `gcd`, `evenodd`, `99`, `aBc`, `pi`, `100`, `squ`, `multiples`, `divisors`, `frac`, `simplify`, `commondenom`, `frac2dec`, `dec2frac`, `compare`, `mixed` (basic two-term plus multi-term/mixed-operator/`reducible_mode`), and the plain/tree/flat-multi-term/`--missing-value`/`--vertical`/`--intermediate` `ope` variants — dispatch to `backend/three_layer_renderer.py`'s `render_worksheet_pdf` (`100`, issue #229, uses a single unnumbered full-content-area layout since its hundred-square grid has no per-problem numbering; `ope --missing-value`, issue #223, is content-format pattern 2; `compare`, issue #224, is content-format pattern 3; `commondenom`, issue #225, ports content-format pattern 4c as-is; `ope --vertical`, issue #227, is content-format pattern 6 and uses `grid_layout='tabular'` for its multi-row xlop/longdivision output; `ope --intermediate`, issue #226, ports content-format pattern 5 as-is, `mul`-only with a single-digit second operand). A request no builder handles (an invalid combination such as `mixed` + `reducible_mode` + a multi-term option, or an unknown `command_type`) returns an explicit HTTP 500 rather than falling through to a subprocess. The legacy subprocess path (`renderers.build_command` / `renderers.run`) and its `_USE_LEGACY_PDF_PIPELINE` source switch were removed in issue #297 (issue #174's 段3); `backend/renderers.py` was renamed to `backend/renderer_config.py`, now just renderer-name resolution plus the shared `RendererRequest` type. The `NUTS_CALC_RENDERER` selection mechanism remains as an extension point for a future renderer. The former `frontend/spa` was the only frontend with a UI path to `command_type: 'com'`; `frontend/web` has none, and none to `command_type: 'pi'` either. `frontend/web` calls `POST /generate-pdf` and `GET /renderer-info`, and is an independent npm project. It additionally calls `POST /generate-problems` (issue #138) to fetch live-generated example problems as JSON; `backend/problem_generation.py` serves those by calling the CLI's data-generation functions in-process. See `docs/L3_implementation/api.md`.
*   **Batch**: `backend/factory.sh` is a third, batch-oriented entry point that calls `nuts_calc_tex.py` repeatedly to populate a `dist/` directory with a fixed set of worksheets.

`nuts_calc_tex.py` implements twenty commands: seven with 1:1 semantics to the removed `nuts_calc.py`, the LaTeX-only `frac`, `mixed`, and `compare` commands, the LaTeX-only `evenodd`, `multiples`, and `divisors` number-property commands, the LaTeX-only `lcm` and `gcd` pair-number commands, and the LaTeX-only `simplify`, `commondenom`, `frac2dec`, `dec2frac`, and `divfrac` fraction/decimal conversion commands. It also owns decimal, written-calculation, and carry-aware drill behavior. Its LaTeX compilation step is pluggable via a `LatexEngineAdapter` (`NUTS_CALC_TEX_ENGINE`, default `lualatex` as of issue #186); the Japanese-capable `lualatex` adapter is the default (see Installation above), and `pdflatex` remains available via `NUTS_CALC_TEX_ENGINE=pdflatex`, though existing English-label workarounds for `pdflatex`'s lack of CJK font support are unchanged by either engine. See `docs/L3_implementation/backend/nuts_calc_tex.py.md`.

See `docs/L1_project/project_overview.md` and `docs/L0_concept/concept.md` for the full breakdown and file/line references.

## Design Principles

*   **Renderer-owned drill logic.** The web backend does not duplicate worksheet-generation rules; it dispatches every PDF request to `three_layer_renderer.py`, which calls `nuts_calc_tex.py`'s data and presentation APIs in-process. The former CLI/subprocess renderer path was deleted in issue #297.
*   **No dependency pinning on the Python side.** There is no lock file, `requirements.txt`, or `pyproject.toml`; dependencies are installed ad hoc. This reflects the project's scope as a small personal/batch-generation tool rather than a deployed service.
*   **Local tests are the current quality gate (no CI yet).** pytest covers both generators and backend translation; Node's built-in test runner covers `frontend/web`'s own `drillPresets.test.js` (issue #98). Renderer-dependent tests compile PDF/CSV output when dependencies are available.
*   **One frontend, no shared package.** `frontend/web` was added as a lightweight (no React, no i18n library, Japanese-only) alternative to the former `frontend/spa` (removed in issue #233), built as a genuine static multi-page site rather than a single-page JS router. It is an independent npm project; its `verticalLayout.js` still duplicates the former `frontend/spa`'s copy, but its drill-menu data model (`drillPresets.js`) diverged from `frontend/spa`'s in issue #98 to match `docs/uiux/calculation_drill_menu_parameters_v1.md` exactly. It does not depend on a shared internal package, anticipating a possible future split of `backend`/`frontend` into separate repositories.

## License
MIT License
