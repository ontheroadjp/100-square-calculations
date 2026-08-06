#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nuts_calc_tex.py -- Phase 1 CLI/PDF foundation (issue #20) + Phase 2 `ope`
command (issue #21) + Phase 3 `com` command (issue #22) + Phase 4 `100`
command (issue #23) + Phase 5 `99` command (issue #24) + Phase 6 `aBc`
command (issue #25) + Phase 7 `squ` command (issue #26) + Phase 8 `pi`
command (issue #27).

A 100%-LaTeX-rendered, fully independent reimplementation of nuts_calc.py's
CLI surface (see the tracking issue #19). This file has zero code
dependency on nuts_calc.py: no imports, no shared modules -- the two are
meant to run side by side, each self-contained.

`ope` (horizontal and --vertical, all operators plus mix, --intermediate),
`com` (complement-to-target), `100` (100-square addition table), `99`
(times-table / kuku, with --descend/--reverse/--shuffle ordering), `aBc`
(mental-arithmetic digit-pair conversion), `squ` (square numbers, with
--descend/--reverse/--shuffle ordering), and `pi` (multiplication by pi,
with the same --descend/--reverse/--shuffle ordering) are all implemented.

Requires a LaTeX distribution (`pdflatex`) on PATH. The `longdivision`
CTAN package (used by `ope --vertical -o div`) is vendored into this repo
under `vendor/texmf/` and located via TEXINPUTS, so no manual TeX package
installation is required beyond a base LaTeX distribution that also
includes `xlop` (e.g. `texlive-latex-base` + `texlive-latex-extra`).
"""

import argparse
import csv
import os
import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable


MIN_ROWS_OR_COLUMNS = 1
DEFAULT_ROWS = 10
PAGE_SIDE_MARGIN_MM = 15
PAGE_TOP_MARGIN_MM = 20
PAGE_BOTTOM_MARGIN_MM = 40
FOOTER_TEXT_LOWERING_MM = 20
VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE = {
    'a3': 4,
    'a4': 4,
    'b5': 2,
    'a4l': 2,
}
ROW_VSPACE_EM = 2.0
MAX_OPERAND_RETRY_ATTEMPTS = 1000
INTERMEDIATE_SINGLE_DIGIT_MAX = 9
MIN_COMPLEMENT_TARGET = 2
ABC_DIGIT_MAX = 9
TABCOLSEP_COUNT_PER_COLUMN = 2
MAX_HUNDRED_SQUARE_DIGITS = 3
HUNDRED_SQUARE_SIZE = 10
HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR = 2
HUNDRED_SQUARE_HEADER_COLOR = 'lightgray'
PI_MULTIPLIER = 3.14
MIN_FRACTION_DIGITS = 1
MAX_FRACTION_DIGITS = 3
BLANK_ANSWER_TEX = '\\hspace{1.5em}'
COM_BLANK_ANSWER_TEX = '\\vcenter{\\hbox{\\fbox{\\rule{0pt}{1em}\\hspace{1em}}}}'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_TEXMF_DIR = os.path.join(SCRIPT_DIR, 'vendor', 'texmf')

OPERATOR_TEX_SYMBOLS = {'add': '+', 'sub': '-', 'mul': '\\times', 'div': '\\div'}
MIX_OPERATORS = ['add', 'sub', 'mul', 'div']
XLOP_VERTICAL_COMMANDS = {'add': 'opadd', 'sub': 'opsub', 'mul': 'opmul'}
XLOP_VERTICAL_LAYOUT_OPTIONS = 'voperator=bottom,columnwidth=2ex'

PAPER_SIZE_TO_GEOMETRY_OPTION = {
    'a3': 'a3paper',
    'a4': 'a4paper',
    'b5': 'b5paper',
    'a4l': 'a4paper,landscape',
}

HEADER_STR = 'Nuts Education'
TITLE_STR = '100 square calculations'
SUB_TITLE_STR = 'for Mental Arithmetic'
COPYRIGHT_STR = 'Copyright(c) 2024 Nuts Education'


def failure(message: str) -> None:
    print(message)
    exit(1)


def _init() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Defined independently of nuts_calc.py's `_init()` (no shared code), but
    mirrors its flag surface for a familiar CLI. `command`/`operator` are
    fully dispatched on for `ope`, `com`, `100`, `99`, `aBc`, `squ`, and
    `pi`.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s A4 | B5",
        description="""
            LaTeX-rendered calculation practice printout generator
            (independent reimplementation of nuts_calc.py).
        """,
        add_help=True,
        epilog="end"
    )
    parser.add_argument('paper_size'
        , type = str
        , choices = ['A3', 'A4', 'B5', 'a3', 'a4', 'b5', 'a4l']
        , help = 'Paper size of prints to be output'
    )
    parser.add_argument('command'
        , type = str
        , choices = ['ope', 'com', '100', '99', 'aBc', 'squ', 'pi', 'frac']
        , help = 'Type of formula to output (including "frac" for fraction arithmetic)'
    )
    parser.add_argument('-a', '--a-value'
        , type = int
        , help = 'Number of digits in the first term of the formula'
    )
    parser.add_argument('-b', '--b-value'
        , type = int
        , help = 'The number of digits in the second term of the formula'
    )
    parser.add_argument('--a-min'
        , type = int
        , default = 1
        , help = 'Minimum value of the first term of the formula'
    )
    parser.add_argument('--a-max'
        , type = int
        , default = 9
        , help = 'Maximum value of the first term of the formula'
    )
    parser.add_argument('--b-min'
        , type = int
        , default = 1
        , help = 'Minimum value of the second term of the formula'
    )
    parser.add_argument('--b-max'
        , type = int
        , default = 9
        , help = 'Maximum value of the second term of the formula'
    )
    parser.add_argument('-o', '--operator'
        , default = ['add']
        , choices = ['add', 'sub', 'mul', 'div', 'mix']
        , nargs="*"
        , help = 'Types of operations included in formulas'
    )
    parser.add_argument('--numerator-digits'
        , type = int
        , default = 1
        , help = 'Number of digits in fraction numerators (frac only)'
    )
    parser.add_argument('--denominator-digits'
        , type = int
        , default = 1
        , help = 'Number of digits in fraction denominators (frac only)'
    )
    parser.add_argument('--same-denominator'
        , default = False
        , action = 'store_true'
        , help = 'Use the same denominator for both fraction operands (frac only)'
    )
    parser.add_argument('--different-denominators'
        , default = False
        , action = 'store_true'
        , help = 'Require different denominators for the two fraction operands (frac only)'
    )
    parser.add_argument('--proper-operands'
        , default = False
        , action = 'store_true'
        , help = 'Use proper fractions for both operands (frac only)'
    )
    parser.add_argument('--proper-result'
        , default = False
        , action = 'store_true'
        , help = 'Only generate positive proper-fraction answers (frac only)'
    )
    parser.add_argument('--descend'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in descending order'
    )
    parser.add_argument('--reverse'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in reverse order'
    )
    parser.add_argument('--shuffle'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in random order'
    )
    parser.add_argument('--intermediate'
        , default = False
        , action = 'store_true'
        , help = 'Write an intermediate formula'
    )
    parser.add_argument('--vertical'
        , default = False
        , action = 'store_true'
        , help = 'Output "ope" problems in vertical (written-calculation, hissan) format'
    )
    parser.add_argument('-r', '--rows'
        , type = int
        , default = None
        , help = 'Lines of question per page'
    )
    parser.add_argument('-c', '--columns'
        , type = int
        , default = 2
        , help = 'Number of columns of questions per page'
    )
    parser.add_argument('-ww', '--with-bottom-answer'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to post answers at the bottom of the page'
    )
    parser.add_argument('-p', '--page'
        , type = int
        , default = 1
        , help = 'Number of pages included in the output file'
    )
    parser.add_argument('-m', '--merge'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to merge the answer pages into the same PDF'
    )
    parser.add_argument('--csv'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to output csv raw data'
    )
    parser.add_argument('--out-file'
        , default = 'result.pdf'
        , help = 'Output file path'
    )
    parser.add_argument('--debug'
        , default = False
        , action = 'store_true'
        , help = 'Enable debug mode'
    )
    args = parser.parse_args()

    if args.rows is None:
        if args.command == 'ope' and args.vertical:
            args.rows = VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE[args.paper_size.lower()]
        else:
            args.rows = DEFAULT_ROWS

    def set_min_max_value(value: int) -> list[int]:
        digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
        min_val, max_val = digits_list[value - 1]
        return [min_val, max_val]

    if args.command == '100':
        # Validated before set_min_max_value() is called below: that function
        # indexes digits_list with value - 1 and raises an unhandled
        # IndexError for value > 5, and silently wraps around to the wrong
        # (5-digit) range for value <= 0 (negative indexing) -- both must be
        # rejected with a clean CLI error first.
        if (args.a_value is not None and not 1 <= args.a_value <= MAX_HUNDRED_SQUARE_DIGITS) \
                or (args.b_value is not None and not 1 <= args.b_value <= MAX_HUNDRED_SQUARE_DIGITS):
            failure(
                f"-a/--a-value and -b/--b-value must be between 1 and "
                f"{MAX_HUNDRED_SQUARE_DIGITS} digits for the '100' command."
            )

    if args.command in ('ope', '100'):
        if args.a_value is not None:
            args.a_min, args.a_max = set_min_max_value(args.a_value)
        if args.b_value is not None:
            args.b_min, args.b_max = set_min_max_value(args.b_value)

    if args.rows < MIN_ROWS_OR_COLUMNS or args.columns < MIN_ROWS_OR_COLUMNS:
        failure(f"-r/--rows and -c/--columns must be at least {MIN_ROWS_OR_COLUMNS}.")

    if args.page < 1:
        failure("-p/--page must be at least 1.")

    if args.command == 'com':
        if args.a_value is None:
            failure("-a/--a-value (complement target) is required for the 'com' command.")
        if args.a_value < MIN_COMPLEMENT_TARGET:
            failure(f"-a/--a-value (complement target) must be at least {MIN_COMPLEMENT_TARGET} for the 'com' command.")

    if args.command == '99':
        if args.a_value is None:
            failure("-a/--a-value (times-table row) is required for the '99' command.")

    if args.command == 'squ':
        if args.a_value is None:
            failure("-a/--a-value (starting square number) is required for the 'squ' command.")

    if args.command == 'pi':
        if args.a_value is None:
            failure("-a/--a-value (starting multiplicand) is required for the 'pi' command.")

    if args.command == 'frac':
        if args.same_denominator and args.different_denominators:
            failure("--same-denominator and --different-denominators cannot be combined.")
        for option_name, value in (
            ('--numerator-digits', args.numerator_digits),
            ('--denominator-digits', args.denominator_digits),
        ):
            if not MIN_FRACTION_DIGITS <= value <= MAX_FRACTION_DIGITS:
                failure(
                    f"{option_name} must be between {MIN_FRACTION_DIGITS} "
                    f"and {MAX_FRACTION_DIGITS} for the 'frac' command."
                )
        if args.proper_operands and args.numerator_digits > args.denominator_digits:
            failure(
                "--proper-operands requires --numerator-digits to be no greater "
                "than --denominator-digits."
            )

    if args.intermediate:
        if args.command != 'ope':
            failure("--intermediate is only supported for the 'ope' command.")
        if args.vertical:
            failure("--intermediate cannot be combined with --vertical.")
        if args.operator != ['mul']:
            failure("--intermediate only supports a single 'mul' operator (use -o mul).")
        if args.b_max > INTERMEDIATE_SINGLE_DIGIT_MAX:
            failure("--intermediate only supports a single-digit second operand (use -b 1 or --b-max <= 9).")

    return args


@dataclass
class Page:
    """
    One page's worth of renderable LaTeX content.

    Attributes:
        blocks: One LaTeX snippet per problem, laid out `columns`-wide.
        columns: Number of columns to arrange `blocks` into.
        bottom_answer_tex: Optional LaTeX snippet appended near the page
            bottom (e.g. a compact answer-key line); `None` to omit it.
        layout: 'inline' (a full-width grid for horizontal-format problems),
            'tabular' (a LaTeX tabular grid with one block per cell, used by
            --vertical hissan blocks so multi-row blocks like
            xlop/longdivision output stay column-aligned), or 'block' (one
            self-contained LaTeX block, used by the 100-square table).
    """
    blocks: list[str] = field(default_factory=list)
    columns: int = 1
    bottom_answer_tex: str | None = None
    layout: str = 'inline'


def build_preamble_tex(paper_size: str) -> str:
    geometry_option = PAPER_SIZE_TO_GEOMETRY_OPTION[paper_size.lower()]
    return (
        "\\documentclass[12pt]{article}\n"
        f"\\usepackage[{geometry_option},margin={PAGE_SIDE_MARGIN_MM}mm,top={PAGE_TOP_MARGIN_MM}mm,"
        f"bottom={PAGE_BOTTOM_MARGIN_MM}mm]{{geometry}}\n"
        "\\usepackage{longdivision}\n"
        "\\usepackage{xlop}\n"
        "\\usepackage{array}\n"
        "\\usepackage[table]{xcolor}\n"
        "\\usepackage{fancyhdr}\n"
        "\\pagestyle{fancy}\n"
        "\\fancyhf{}\n"
        f"\\fancyfoot[L]{{{COPYRIGHT_STR}}}\n"
        "\\fancyfoot[R]{Page \\#\\thepage}\n"
        "\\renewcommand{\\headrulewidth}{0pt}\n"
        "\\renewcommand{\\footrulewidth}{0pt}\n"
        f"\\addtolength{{\\footskip}}{{{FOOTER_TEXT_LOWERING_MM}mm}}\n"
        "\\setlength{\\parindent}{0pt}\n"
    )


def build_page_header_tex() -> str:
    return (
        f"{{\\bfseries {HEADER_STR}}}\\\\\n"
        f"{{\\Large\\bfseries {TITLE_STR}}}\\\\\n"
        f"{{\\small {SUB_TITLE_STR}}}\\\\[1em]\n"
        "Date: \\underline{\\hspace{4cm}} \\hfill Time: \\underline{\\hspace{4cm}}\n"
        "\\vspace{1.5em}\n\n"
    )


def build_inline_grid_tex(blocks: list[str], columns: int) -> str:
    """Lay out horizontal problem rows across the full page body.

    Each visual row uses equal-width cells spanning ``\\textwidth``, keeping
    each problem centered in its allocated column regardless of the number
    of columns. ``\\vfill`` before every row lets TeX distribute the
    remaining printable height between the header, rows, optional bottom
    answer, and footer area.
    """
    column_width_tex = (
        f"\\dimexpr(\\textwidth-{TABCOLSEP_COUNT_PER_COLUMN * columns}\\tabcolsep)/{columns}\\relax"
    )
    column_spec = f">{{\\centering\\arraybackslash}}p{{{column_width_tex}}}" * columns
    row_tabulars = []
    for row_blocks in build_column_major_rows(blocks, columns):
        row_blocks += [''] * (columns - len(row_blocks))
        row_tex = ' & '.join(row_blocks)
        row_tabulars.append(
            "\\vfill\n"
            f"\\noindent\\begin{{tabular}}{{{column_spec}}}\n{row_tex}\\\\\n\\end{{tabular}}"
        )
    return '\n'.join(row_tabulars)


def build_column_major_rows(blocks: list[str], columns: int) -> list[list[str]]:
    """Convert sequential blocks to visual rows filled down each column first."""
    row_count = (len(blocks) + columns - 1) // columns
    return [
        [
            blocks[column * row_count + row]
            for column in range(columns)
            if column * row_count + row < len(blocks)
        ]
        for row in range(row_count)
    ]


def build_tabular_grid_tex(blocks: list[str], columns: int) -> str:
    """
    Arrange blocks into rows of a LaTeX tabular, one block per cell.

    Used for --vertical blocks (xlop/longdivision output), which are
    multi-row LaTeX content that would break \\hspace-based inline joining
    (build_inline_grid_tex); a tabular cell keeps each block's rows
    self-contained and column-aligned regardless of its neighbors' height.
    Column width is computed from \\textwidth so the grid adapts to the
    page's paper size and column count, with \\tabcolsep padding
    subtracted to avoid an overfull row.

    Each row is emitted as its own single-row tabular, joined by the same
    \\par\\vspace break build_inline_grid_tex uses between rows, rather
    than one tabular spanning every row: a plain `tabular` cannot break
    across a page boundary, so a tall multi-row grid (e.g. the default
    10 rows) would otherwise be pushed as one unbreakable block, leaving
    the current page blank and overflowing past the next page's bottom
    margin instead of just flowing onto it row by row.
    """
    column_width_tex = (
        f"\\dimexpr(\\textwidth-{TABCOLSEP_COUNT_PER_COLUMN * columns}\\tabcolsep)/{columns}\\relax"
    )
    column_spec = f">{{\\centering\\arraybackslash}}p{{{column_width_tex}}}" * columns
    row_tabulars = []
    for row_blocks in build_column_major_rows(blocks, columns):
        row_blocks += [''] * (columns - len(row_blocks))
        row_tex = ' & '.join(row_blocks)
        row_tabulars.append(f"\\begin{{tabular}}{{{column_spec}}}\n{row_tex}\n\\end{{tabular}}")
    return f"\\par\\vspace{{{ROW_VSPACE_EM}em}}\n".join(row_tabulars)


def build_block_grid_tex(blocks: list[str]) -> str:
    """Vertically center self-contained blocks without nesting LaTeX tables."""
    return "\\vfill\n" + "\n".join(blocks) + "\n\\vfill"


def build_page_tex(page: Page) -> str:
    """Render one Page's grid of blocks, plus header and optional bottom answer."""
    if page.layout == 'tabular':
        grid_tex = build_tabular_grid_tex(page.blocks, page.columns)
    elif page.layout == 'block':
        grid_tex = build_block_grid_tex(page.blocks)
    else:
        grid_tex = build_inline_grid_tex(page.blocks, page.columns)

    parts = [build_page_header_tex(), grid_tex]
    if page.bottom_answer_tex:
        parts.append(f"\\vfill\n{{\\small {page.bottom_answer_tex}}}\n")
    return "\n".join(parts)


def build_document_tex(paper_size: str, blank_pages: list[Page], filled_pages: list[Page], mode: str) -> str:
    """
    Build a full LaTeX document.

    Args:
        mode: 'blank' (practice sheet only), 'filled' (worked answer key
            only), or 'merge' (each blank page immediately followed by its
            filled counterpart, in one PDF -- a simplified variant of
            nuts_calc.py's `--merge`, which instead delays the answer page
            by one page; see module/L3 docs for details).
    """
    if mode == 'blank':
        ordered_pages = blank_pages
    elif mode == 'filled':
        ordered_pages = filled_pages
    else:
        ordered_pages = []
        for blank_page, filled_page in zip(blank_pages, filled_pages):
            ordered_pages.append(blank_page)
            ordered_pages.append(filled_page)

    document_body = "\n\\newpage\n".join(build_page_tex(page) for page in ordered_pages)
    return (
        build_preamble_tex(paper_size)
        + "\\begin{document}\n"
        + document_body
        + "\n\\end{document}\n"
    )


def compile_tex(tex_source: str, out_pdf_path: str) -> None:
    env = os.environ.copy()
    env['TEXINPUTS'] = f"{VENDOR_TEXMF_DIR}//:" + env.get('TEXINPUTS', '')
    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, 'worksheet.tex')
        with open(tex_path, 'w') as f:
            f.write(tex_source)
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'worksheet.tex'],
            cwd=tmp_dir, env=env, capture_output=True, text=True,
        )
        if result.returncode != 0:
            failure(f"pdflatex failed while building {out_pdf_path}:\n{result.stdout[-4000:]}")
        shutil.copyfile(os.path.join(tmp_dir, 'worksheet.pdf'), out_pdf_path)


def write_csv(rows: list[list[object]], csv_path: str) -> None:
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


@dataclass
class OpeProblem:
    """One generated `ope` (add/sub/mul/div) arithmetic problem."""
    index: int
    a: int
    b: int
    operator: str
    c: int


def calc_add(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    return a, b, a + b


def calc_sub(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    """
    Retry with freshly-sampled operands until the result is positive.

    Random sampling alone can fail within MAX_OPERAND_RETRY_ATTEMPTS even
    when a valid pair exists, if the valid-pair space is a small fraction
    of nums_a x nums_b (e.g. nums_a=[1..1000], nums_b=[999, 1000] has only
    one positive-result pair). Falling back to the extreme pair
    (max(nums_a), min(nums_b)) -- the easiest positive-result pair to
    construct -- guarantees success whenever any solution exists, while
    keeping the random attempts for the common case's variety.
    """
    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if a - b > 0:
            return a, b, a - b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    a, b = max(nums_a), min(nums_b)
    if a - b > 0:
        return a, b, a - b
    raise ValueError(
        "No subtraction pair with a positive result (a - b > 0) "
        "found in the given number ranges."
    )


def calc_mul(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    return a, b, a * b


def find_exact_division_pair(nums_a: list[int], nums_b: list[int]) -> tuple[int, int] | None:
    """
    Deterministically find one (a, b) pair with b != 0 and a % b == 0.

    Used as calc_div's fallback when MAX_OPERAND_RETRY_ATTEMPTS of random
    sampling doesn't find a solution (possible when the valid-pair space
    is a small fraction of nums_a x nums_b). For each candidate divisor,
    only its multiples within the nums_a range are probed (not every
    nums_a element), so this stays cheap even for large ranges.
    """
    if not nums_a:
        return None
    nums_a_set = set(nums_a)
    a_min, a_max = min(nums_a_set), max(nums_a_set)
    for b in nums_b:
        if b == 0:
            continue
        first_multiple = -(-a_min // b) * b  # ceiling division
        for candidate in range(first_multiple, a_max + 1, abs(b)):
            if candidate in nums_a_set:
                return candidate, b
    return None


def calc_div(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    """
    Retry with freshly-sampled operands until the division is exact.

    Falls back to find_exact_division_pair (see its docstring) if random
    sampling exhausts MAX_OPERAND_RETRY_ATTEMPTS without success.
    """
    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if b != 0 and a % b == 0:
            return a, b, a // b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    fallback = find_exact_division_pair(nums_a, nums_b)
    if fallback is not None:
        a, b = fallback
        return a, b, a // b
    raise ValueError(
        "No exact-division pair (a % b == 0, b != 0) found in the given number ranges."
    )


CALC_FUNCTIONS: dict[str, Callable[[int, int, list[int], list[int]], tuple[int, int, int]]] = {
    'add': calc_add,
    'sub': calc_sub,
    'mul': calc_mul,
    'div': calc_div,
}


def generate_ope_problems(
        nums_a: list[int], nums_b: list[int], operators: list[str],
        order: int, start_index: int
    ) -> list[OpeProblem]:
    """
    Generate `order` arithmetic problems starting at `start_index`.

    `operators=['mix']` picks a random operator (add/sub/mul/div) per
    problem; otherwise one operator is picked per problem from `operators`.
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        a = random.choice(nums_a)
        b = random.choice(nums_b)
        operator = random.choice(effective_operators)
        a, b, c = CALC_FUNCTIONS[operator](a, b, nums_a, nums_b)
        problems.append(OpeProblem(index=start_index + offset, a=a, b=b, operator=operator, c=c))
    return problems


def build_horizontal_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """Render one `ope` problem in horizontal format: `n) $a op b = c$`."""
    symbol = OPERATOR_TEX_SYMBOLS[problem.operator]
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.a} {symbol} {problem.b} = {result_tex}$"


def build_intermediate_memo(a: int, b: int) -> str:
    """
    2-digit x 1-digit mental-math memo technique (see memo.md STEP 1):
    concatenate (tens digit of a) x b and (ones digit of a) x b, each
    zero-padded to 2 digits.
    """
    tens_digit, ones_digit = divmod(a, 10)
    return f"{tens_digit * b:02d}{ones_digit * b:02d}"


def build_horizontal_intermediate_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """Render one `ope --intermediate` problem: `n) $a * b => memo => c$`."""
    memo = build_intermediate_memo(problem.a, problem.b)
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.a} \\times {problem.b} \\Rightarrow {memo} \\Rightarrow {result_tex}$"


def build_vertical_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """
    Render one `ope --vertical` (hissan) problem as a tabular-cell block:
    index label, then the LaTeX-rendered written-calculation layout.

    add/sub/mul use the `xlop` package (auto-rendering carries and, for a
    multi-digit multiplier, one partial-product row per digit). div uses
    `longdivision`. For the blank (practice) variant, xlop's per-digit
    style hooks (resultstyle/carrystyle/intermediarystyle) are overridden
    to `\\phantom`, which reserves the digits' layout space without
    printing them; longdivision has an equivalent built-in via its
    `stage=0` option (only the bracket/divisor/dividend are shown).
    """
    index_line = f"{problem.index})\\newline "
    if problem.operator == 'div':
        stage_option = '' if show_answer else '[stage=0]'
        return f"{index_line}\\[\\intlongdivision{stage_option}{{{problem.a}}}{{{problem.b}}}\\]"

    command = XLOP_VERTICAL_COMMANDS[problem.operator]
    op_call_tex = f"\\[\\{command}{{{problem.a}}}{{{problem.b}}}\\]"
    if show_answer:
        return (
            index_line
            + f"\\begingroup\\opset{{{XLOP_VERTICAL_LAYOUT_OPTIONS}}}"
            + op_call_tex
            + "\\endgroup"
        )
    return (
        index_line
        + "\\begingroup\\opset{"
        + XLOP_VERTICAL_LAYOUT_OPTIONS
        + ",resultstyle=\\phantom,carrystyle=\\phantom,intermediarystyle=\\phantom}"
        + op_call_tex
        + "\\endgroup"
    )


def build_ope_page_pair(problems: list[OpeProblem], columns: int, vertical: bool, intermediate: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `ope` problems."""
    if vertical:
        block_builder: Callable[[OpeProblem, bool], str] = build_vertical_block_tex
        layout = 'tabular'
    elif intermediate:
        block_builder = build_horizontal_intermediate_block_tex
        layout = 'inline'
    else:
        block_builder = build_horizontal_block_tex
        layout = 'inline'

    blank_page = Page(
        blocks=[block_builder(problem, show_answer=False) for problem in problems],
        columns=columns, layout=layout,
    )
    filled_page = Page(
        blocks=[block_builder(problem, show_answer=True) for problem in problems],
        columns=columns, layout=layout,
    )
    return blank_page, filled_page


def build_ope_bottom_answer_tex(problems: list[OpeProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_ope_csv_rows(pages_problems: list[list[OpeProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.operator, problem.b, problem.c])
    return rows


@dataclass
class ComProblem:
    """One generated `com` (complement-to-target) problem: a + c = target."""
    index: int
    a: int
    target: int
    c: int


def generate_com_problems(target: int, order: int, start_index: int) -> list[ComProblem]:
    """
    Generate `order` complement problems starting at `start_index`.

    `a` is drawn from 1..target-1 (inclusive) so the complement `c = target
    - a` is always a positive integer strictly less than `target`.
    """
    seed = list(range(1, target))
    problems = []
    for offset in range(order):
        a = random.choice(seed)
        problems.append(ComProblem(index=start_index + offset, a=a, target=target, c=target - a))
    return problems


def build_com_block_tex(problem: ComProblem, show_answer: bool) -> str:
    """Render one `com` problem with a boxed missing operand in the blank version."""
    result_tex = str(problem.c) if show_answer else COM_BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.a} + {result_tex} = {problem.target}$"


def build_com_page_pair(problems: list[ComProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `com` problems."""
    blank_page = Page(
        blocks=[build_com_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_com_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_com_bottom_answer_tex(problems: list[ComProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_com_csv_rows(pages_problems: list[list[ComProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.target, problem.c])
    return rows


def build_com_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[ComProblem]]]:
    """Generate real `com` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_com_problems(ini.a_value, order, start_index)
        blank_page, filled_page = build_com_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_com_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class HundredSquareTable:
    """One generated `100` addition table: left_values[r] + top_values[c] = the (r, c) cell."""
    left_values: list[int]
    top_values: list[int]

    @property
    def answers(self) -> list[list[int]]:
        return [[left + top for top in self.top_values] for left in self.left_values]


def sample_hundred_square_values(nums: list[int]) -> list[int]:
    """
    Sample HUNDRED_SQUARE_SIZE values for one axis of the addition table.

    The candidate list is duplicated HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR
    times before sampling without replacement, so a value can appear at
    most twice: needed because the default digit-1 range (1-9, nine
    distinct values) is smaller than the ten slots the table requires
    (mirrors nuts_calc.py's `100` square generation).
    """
    seed = nums * HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR
    return random.sample(seed, HUNDRED_SQUARE_SIZE)


def generate_hundred_square(nums_left: list[int], nums_top: list[int]) -> HundredSquareTable:
    return HundredSquareTable(
        left_values=sample_hundred_square_values(nums_left),
        top_values=sample_hundred_square_values(nums_top),
    )


def build_hundred_square_block_tex(table: HundredSquareTable, show_answer: bool) -> str:
    """
    Render one addition table as an (HUNDRED_SQUARE_SIZE+1)-square LaTeX
    tabular: a blank top-left corner, a shaded header row (table.top_values)
    and header column (table.left_values), and a HUNDRED_SQUARE_SIZE x
    HUNDRED_SQUARE_SIZE grid of data cells (left+top sums when show_answer,
    otherwise blank for the student to fill in).
    """
    column_spec = f">{{\\columncolor{{{HUNDRED_SQUARE_HEADER_COLOR}}}}}c|" + "c" * HUNDRED_SQUARE_SIZE
    header_cells = [''] + [str(value) for value in table.top_values]
    lines = [
        "\\begin{center}",
        f"\\begin{{tabular}}{{|{column_spec}|}}",
        "\\hline",
        f"\\rowcolor{{{HUNDRED_SQUARE_HEADER_COLOR}}} {' & '.join(header_cells)} \\\\",
        "\\hline",
    ]
    for left, answer_row in zip(table.left_values, table.answers):
        data_cells = [str(value) for value in answer_row] if show_answer else [''] * HUNDRED_SQUARE_SIZE
        lines.append(' & '.join([str(left)] + data_cells) + " \\\\")
        lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{center}")
    return "\n".join(lines)


def build_hundred_square_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[HundredSquareTable]]:
    """
    Generate real `100` addition tables and their blank/filled Page pairs.

    One table per page (`ini.page` controls the page count); `ini.rows`/
    `ini.columns`/`ini.with_bottom_answer` are accepted but unused for this
    command, matching nuts_calc.py's original `100` behavior (a single
    fixed-size 100-square table per page, no bottom answer strip).
    """
    nums_left = list(range(ini.a_min, ini.a_max + 1))
    nums_top = list(range(ini.b_min, ini.b_max + 1))

    blank_pages = []
    filled_pages = []
    pages_tables = []
    for _ in range(ini.page):
        table = generate_hundred_square(nums_left, nums_top)
        pages_tables.append(table)
        blank_pages.append(
            Page(blocks=[build_hundred_square_block_tex(table, show_answer=False)], columns=1, layout='block')
        )
        filled_pages.append(
            Page(blocks=[build_hundred_square_block_tex(table, show_answer=True)], columns=1, layout='block')
        )

    return blank_pages, filled_pages, pages_tables


def build_hundred_square_csv_rows(pages_tables: list[HundredSquareTable]) -> list[list[object]]:
    """One header row (`top_values`) plus one row per left value per page, each prefixed with the page number."""
    rows: list[list[object]] = []
    for page_number, table in enumerate(pages_tables, start=1):
        rows.append([page_number, ''] + table.top_values)
        for left, answer_row in zip(table.left_values, table.answers):
            rows.append([page_number, left] + answer_row)
    return rows


@dataclass
class KukuProblem:
    """One generated `99` (times-table / kuku) problem: a x b = c, with `a` fixed for a whole page."""
    index: int
    a: int
    b: int
    c: int


def generate_kuku_problems(a_value: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[KukuProblem]:
    """
    Generate `order` times-table problems for the fixed row `a_value`, starting at `start_index`.

    The multiplier `b` is drawn from the base sequence `1..order` -- an
    independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == '99'` branch (`nuts_calc.py:508-522`), which likewise ties the
    multiplier range to the page's row count rather than capping it at 9, so
    `b` can exceed 9 when `order > 9`. `descend` reverses that sequence
    (`order..1`); `shuffle` randomizes it after any `descend` reversal,
    matching nuts_calc.py's `num_list.reverse()` then `random.shuffle()`
    ordering (`nuts_calc.py:513-516`).
    """
    multipliers = list(range(1, order + 1))
    if descend:
        multipliers.reverse()
    if shuffle:
        random.shuffle(multipliers)
    return [
        KukuProblem(index=start_index + offset, a=a_value, b=b, c=a_value * b)
        for offset, b in enumerate(multipliers)
    ]


def build_kuku_block_tex(problem: KukuProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `99` problem: `n) $a \\times b = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times b$`,
    inferred from nuts_calc.py's `is_reverse` branch reordering `vals_c`
    ahead of `vals_a`/`vals_b` (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {problem.b}$"
    return f"{problem.index}) ${problem.a} \\times {problem.b} = {result_tex}$"


def build_kuku_page_pair(problems: list[KukuProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `99` problems."""
    blank_page = Page(
        blocks=[build_kuku_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_kuku_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_kuku_bottom_answer_tex(problems: list[KukuProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_kuku_csv_rows(pages_problems: list[list[KukuProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.b, problem.c])
    return rows


def build_kuku_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[KukuProblem]]]:
    """Generate real `99` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_kuku_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_kuku_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_kuku_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class AbcProblem:
    """
    One generated `aBc` problem: a random 4-digit sequence a/b/c/d (each
    0-9, displayed as `abcd`) converted to its value by adding the two
    digit-pairs `ab` (shifted one place, i.e. `x10`) and `cd`. This is the
    same digit-pair decomposition used by `ope --intermediate`'s
    mental-multiplication memo (`build_intermediate_memo`), drilled here on
    its own as a standalone conversion step (memo.md section 3: converting
    a 4-digit figure into its 3-digit result via digit-pair addition).
    """
    index: int
    a: int
    b: int
    c: int
    d: int

    @property
    def abcd_display(self) -> str:
        return f"{self.a}{self.b}{self.c}{self.d}"

    @property
    def answer(self) -> int:
        return (self.a * 10 + self.b) * 10 + (self.c * 10 + self.d)


def generate_abc_problems(order: int, start_index: int) -> list[AbcProblem]:
    """
    Generate `order` aBc problems starting at `start_index`.

    Each of a/b/c/d is drawn independently from 0..ABC_DIGIT_MAX -- an
    independent reimplementation of nuts_calc.py's `get_aBc_data`
    (`nuts_calc.py:548-587`), which draws the same four digits from the
    same range. Unlike that implementation, `AbcProblem.abcd_display`
    always renders all four digits (`f"{a}{b}{c}{d}"`) instead of only
    zero-padding the single 3-character case (`nuts_calc.py:577-578` only
    handles `len(str(abcd)) == 3`, leaving shorter results un-padded).
    """
    seed = list(range(ABC_DIGIT_MAX + 1))
    problems = []
    for offset in range(order):
        a = random.choice(seed)
        b = random.choice(seed)
        c = random.choice(seed)
        d = random.choice(seed)
        problems.append(AbcProblem(index=start_index + offset, a=a, b=b, c=c, d=d))
    return problems


def build_abc_block_tex(problem: AbcProblem, show_answer: bool) -> str:
    """Render one `aBc` problem: `n) $abcd \\Rightarrow ____$`, filled with the converted answer when show_answer."""
    result_tex = str(problem.answer) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.abcd_display} \\Rightarrow {result_tex}$"


def build_abc_page_pair(problems: list[AbcProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `aBc` problems."""
    blank_page = Page(
        blocks=[build_abc_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_abc_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_abc_bottom_answer_tex(problems: list[AbcProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.answer}" for problem in problems)


def build_abc_csv_rows(pages_problems: list[list[AbcProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index,
                problem.a, problem.b, problem.c, problem.d, problem.answer,
            ])
    return rows


def build_abc_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[AbcProblem]]]:
    """Generate real `aBc` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_abc_problems(order, start_index)
        blank_page, filled_page = build_abc_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_abc_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class SquProblem:
    """One generated `squ` (square numbers) problem: a x a = c."""
    index: int
    a: int
    c: int


def generate_squ_problems(start_num: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[SquProblem]:
    """
    Generate `order` square-number problems starting from `start_num`, with problem numbering starting at `start_index`.

    An independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == 'squ'` branch (`nuts_calc.py:508-526,541-542`): the base
    sequence `start_num..start_num+order-1` is squared (`a = a`, `c = a * a`
    -- `b` is always equal to `a`, so it is not stored separately).
    `descend` reverses that sequence (`start_num+order-1..start_num`);
    `shuffle` randomizes it after any `descend` reversal, matching
    nuts_calc.py's `num_list.reverse()` then `random.shuffle()` ordering.
    """
    sequence = list(range(start_num, start_num + order))
    if descend:
        sequence.reverse()
    if shuffle:
        random.shuffle(sequence)
    return [
        SquProblem(index=start_index + offset, a=a, c=a * a)
        for offset, a in enumerate(sequence)
    ]


def build_squ_block_tex(problem: SquProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `squ` problem: `n) $a \\times a = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times a$`,
    mirroring `build_kuku_block_tex`'s handling of nuts_calc.py's
    `is_reverse` branch (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {problem.a}$"
    return f"{problem.index}) ${problem.a} \\times {problem.a} = {result_tex}$"


def build_squ_page_pair(problems: list[SquProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `squ` problems."""
    blank_page = Page(
        blocks=[build_squ_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_squ_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_squ_bottom_answer_tex(problems: list[SquProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_squ_csv_rows(pages_problems: list[list[SquProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.c])
    return rows


def build_squ_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[SquProblem]]]:
    """Generate real `squ` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_squ_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_squ_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_squ_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


def build_ope_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[OpeProblem]]]:
    """Generate real `ope` problems and their blank/filled Page pairs for every page."""
    nums_a = list(range(ini.a_min, ini.a_max + 1))
    nums_b = list(range(ini.b_min, ini.b_max + 1))
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_ope_problems(nums_a, nums_b, ini.operator, order, start_index)
        blank_page, filled_page = build_ope_page_pair(problems, ini.columns, ini.vertical, ini.intermediate)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_ope_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class PiProblem:
    """One generated `pi` (multiplication by pi) problem: a x PI_MULTIPLIER = c."""
    index: int
    a: int
    c: float


def generate_pi_problems(start_num: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[PiProblem]:
    """
    Generate `order` pi-multiplication problems starting from `start_num`, with problem numbering starting at `start_index`.

    An independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == 'pi'` branch (`nuts_calc.py:508-522,527-530,541-542`): the base
    sequence `start_num..start_num+order-1` is multiplied by `PI_MULTIPLIER`
    (`a = a`, `c = a * PI_MULTIPLIER` -- `b` is always `PI_MULTIPLIER`, so it
    is not stored separately). `descend` reverses that sequence
    (`start_num+order-1..start_num`); `shuffle` randomizes it after any
    `descend` reversal, matching nuts_calc.py's `num_list.reverse()` then
    `random.shuffle()` ordering (same as `generate_squ_problems`).

    `c` is rounded to 2 decimal places: `PI_MULTIPLIER` (3.14) has 2 decimal
    digits, so `a * PI_MULTIPLIER` is mathematically always exact to 2
    decimals, but IEEE 754 float multiplication produces artifacts for some
    `a` (e.g. `5 * 3.14 == 15.700000000000001`) that nuts_calc.py renders
    verbatim; rounding avoids surfacing that artifact in the printed drill.
    """
    sequence = list(range(start_num, start_num + order))
    if descend:
        sequence.reverse()
    if shuffle:
        random.shuffle(sequence)
    return [
        PiProblem(index=start_index + offset, a=a, c=round(a * PI_MULTIPLIER, 2))
        for offset, a in enumerate(sequence)
    ]


def build_pi_block_tex(problem: PiProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `pi` problem: `n) $a \\times 3.14 = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times 3.14$`,
    mirroring `build_squ_block_tex`'s handling of nuts_calc.py's
    `is_reverse` branch (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {PI_MULTIPLIER}$"
    return f"{problem.index}) ${problem.a} \\times {PI_MULTIPLIER} = {result_tex}$"


def build_pi_page_pair(problems: list[PiProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `pi` problems."""
    blank_page = Page(
        blocks=[build_pi_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_pi_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_pi_bottom_answer_tex(problems: list[PiProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_pi_csv_rows(pages_problems: list[list[PiProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.c])
    return rows


def build_pi_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[PiProblem]]]:
    """Generate real `pi` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_pi_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_pi_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_pi_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass(frozen=True)
class FractionOperand:
    """A displayed fraction whose unreduced numerator/denominator are retained."""
    numerator: int
    denominator: int

    @property
    def value(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True)
class FractionProblem:
    """One exact fraction-arithmetic problem."""
    index: int
    a: FractionOperand
    b: FractionOperand
    operator: str
    c: Fraction


def digit_range(digits: int) -> tuple[int, int]:
    """Return the positive integer range having exactly ``digits`` digits."""
    return (1 if digits == 1 else 10 ** (digits - 1), 10 ** digits - 1)


def random_fraction_operand(
        numerator_digits: int, denominator_digits: int, proper: bool,
        denominator: int | None = None,
    ) -> FractionOperand:
    numerator_min, numerator_max = digit_range(numerator_digits)
    denominator_min, denominator_max = digit_range(denominator_digits)
    denominator_min = max(2, denominator_min)
    chosen_denominator = denominator or random.randint(denominator_min, denominator_max)
    if proper:
        numerator_max = min(numerator_max, chosen_denominator - 1)
    if numerator_min > numerator_max:
        raise ValueError("No fraction operand satisfies the requested digit and proper-fraction constraints.")
    return FractionOperand(random.randint(numerator_min, numerator_max), chosen_denominator)


def calculate_fraction(a: Fraction, b: Fraction, operator: str) -> Fraction:
    """Apply one supported operator to two exact fraction values."""
    if operator == 'add':
        return a + b
    if operator == 'sub':
        return a - b
    if operator == 'mul':
        return a * b
    return a / b


def generate_fraction_problems(
        numerator_digits: int, denominator_digits: int, operators: list[str],
        order: int, start_index: int, same_denominator: bool,
        proper_operands: bool, proper_result: bool,
        different_denominators: bool = False,
    ) -> list[FractionProblem]:
    """Generate exact fraction problems satisfying the requested constraints."""
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    denominator_min, denominator_max = digit_range(denominator_digits)
    denominator_min = max(2, denominator_min)
    problems = []
    for offset in range(order):
        operator = random.choice(effective_operators)
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            common_denominator = (
                random.randint(denominator_min, denominator_max)
                if same_denominator else None
            )
            try:
                a = random_fraction_operand(
                    numerator_digits, denominator_digits, proper_operands,
                    common_denominator,
                )
                b = random_fraction_operand(
                    numerator_digits, denominator_digits, proper_operands,
                    common_denominator,
                )
            except ValueError:
                continue
            if different_denominators and a.denominator == b.denominator:
                continue
            c = calculate_fraction(a.value, b.value, operator)
            if c <= 0:
                continue
            if proper_result and c >= 1:
                continue
            problems.append(FractionProblem(start_index + offset, a, b, operator, c))
            break
        else:
            raise ValueError("Unable to generate fraction problems with the requested constraints.")
    return problems


def fraction_to_tex(value: Fraction | FractionOperand) -> str:
    """Render an exact or display-preserving fraction as LaTeX."""
    numerator = value.numerator
    denominator = value.denominator
    if denominator == 1:
        return str(numerator)
    return f"\\frac{{{numerator}}}{{{denominator}}}"


def build_fraction_block_tex(problem: FractionProblem, show_answer: bool) -> str:
    symbol = OPERATOR_TEX_SYMBOLS[problem.operator]
    result_tex = fraction_to_tex(problem.c) if show_answer else BLANK_ANSWER_TEX
    return (
        f"{problem.index}) $\\displaystyle {fraction_to_tex(problem.a)} {symbol} "
        f"{fraction_to_tex(problem.b)} = {result_tex}$"
    )


def build_fraction_page_pair(problems: list[FractionProblem], columns: int) -> tuple[Page, Page]:
    return (
        Page([build_fraction_block_tex(problem, False) for problem in problems], columns),
        Page([build_fraction_block_tex(problem, True) for problem in problems], columns),
    )


def build_fraction_bottom_answer_tex(problems: list[FractionProblem]) -> str:
    return ' \\quad '.join(
        f"({problem.index}) $\\displaystyle {fraction_to_tex(problem.c)}$"
        for problem in problems
    )


def build_fraction_csv_rows(pages_problems: list[list[FractionProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index,
                problem.a.numerator, problem.a.denominator, problem.operator,
                problem.b.numerator, problem.b.denominator,
                problem.c.numerator, problem.c.denominator,
            ])
    return rows


def build_fraction_pages(
        ini: argparse.Namespace,
    ) -> tuple[list[Page], list[Page], list[list[FractionProblem]]]:
    order = ini.rows * ini.columns
    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        problems = generate_fraction_problems(
            ini.numerator_digits, ini.denominator_digits, ini.operator, order,
            (page_number - 1) * order + 1, ini.same_denominator,
            ini.proper_operands, ini.proper_result, ini.different_denominators,
        )
        blank_page, filled_page = build_fraction_page_pair(problems, ini.columns)
        if ini.with_bottom_answer:
            blank_page.bottom_answer_tex = build_fraction_bottom_answer_tex(problems)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)
    return blank_pages, filled_pages, pages_problems


def main(ini: argparse.Namespace) -> None:
    if shutil.which('pdflatex') is None:
        failure(
            "pdflatex not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    ope_pages_problems: list[list[OpeProblem]] | None = None
    com_pages_problems: list[list[ComProblem]] | None = None
    hundred_square_pages_tables: list[HundredSquareTable] | None = None
    kuku_pages_problems: list[list[KukuProblem]] | None = None
    abc_pages_problems: list[list[AbcProblem]] | None = None
    squ_pages_problems: list[list[SquProblem]] | None = None
    pi_pages_problems: list[list[PiProblem]] | None = None
    fraction_pages_problems: list[list[FractionProblem]] | None = None
    if ini.command == 'ope':
        blank_pages, filled_pages, ope_pages_problems = build_ope_pages(ini)
    elif ini.command == 'com':
        blank_pages, filled_pages, com_pages_problems = build_com_pages(ini)
    elif ini.command == '100':
        blank_pages, filled_pages, hundred_square_pages_tables = build_hundred_square_pages(ini)
    elif ini.command == '99':
        blank_pages, filled_pages, kuku_pages_problems = build_kuku_pages(ini)
    elif ini.command == 'aBc':
        blank_pages, filled_pages, abc_pages_problems = build_abc_pages(ini)
    elif ini.command == 'squ':
        blank_pages, filled_pages, squ_pages_problems = build_squ_pages(ini)
    elif ini.command == 'pi':
        blank_pages, filled_pages, pi_pages_problems = build_pi_pages(ini)
    else:
        blank_pages, filled_pages, fraction_pages_problems = build_fraction_pages(ini)

    outfile_basename, _ = os.path.splitext(ini.out_file)
    outfile_read = outfile_basename + '_read.pdf'
    outfile_csv = outfile_basename + '.csv'

    if ini.merge:
        tex_source = build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='merge')
        compile_tex(tex_source, ini.out_file)
    else:
        compile_tex(build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='blank'), ini.out_file)
        compile_tex(build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='filled'), outfile_read)

    if ini.csv:
        if ope_pages_problems is not None:
            rows = build_ope_csv_rows(ope_pages_problems)
        elif com_pages_problems is not None:
            rows = build_com_csv_rows(com_pages_problems)
        elif hundred_square_pages_tables is not None:
            rows = build_hundred_square_csv_rows(hundred_square_pages_tables)
        elif kuku_pages_problems is not None:
            rows = build_kuku_csv_rows(kuku_pages_problems)
        elif abc_pages_problems is not None:
            rows = build_abc_csv_rows(abc_pages_problems)
        elif squ_pages_problems is not None:
            rows = build_squ_csv_rows(squ_pages_problems)
        elif pi_pages_problems is not None:
            rows = build_pi_csv_rows(pi_pages_problems)
        else:
            rows = build_fraction_csv_rows(fraction_pages_problems)
        write_csv(rows, outfile_csv)

    print("export PDF")
    print("All done")


if __name__ == '__main__':
    main(_init())
