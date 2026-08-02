#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nuts_calc_tex.py -- Phase 1 CLI/PDF foundation (issue #20) + Phase 2 `ope`
command (issue #21).

A 100%-LaTeX-rendered, fully independent reimplementation of nuts_calc.py's
CLI surface (see the tracking issue #19). This file has zero code
dependency on nuts_calc.py: no imports, no shared modules -- the two are
meant to run side by side, each self-contained.

`ope` (horizontal and --vertical, all operators plus mix, --intermediate)
is fully implemented. The other six commands (com/100/99/aBc/squ/pi) still
render Phase-1 placeholder content pending later phases (issues #22-#27).

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
from typing import Callable


MIN_ROWS_OR_COLUMNS = 1
BLOCK_GUTTER_CM = 1.0
ROW_VSPACE_EM = 2.0
MAX_OPERAND_RETRY_ATTEMPTS = 1000
INTERMEDIATE_SINGLE_DIGIT_MAX = 9
TABCOLSEP_COUNT_PER_COLUMN = 2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_TEXMF_DIR = os.path.join(SCRIPT_DIR, 'vendor', 'texmf')

OPERATOR_TEX_SYMBOLS = {'add': '+', 'sub': '-', 'mul': '\\times', 'div': '\\div'}
MIX_OPERATORS = ['add', 'sub', 'mul', 'div']
XLOP_VERTICAL_COMMANDS = {'add': 'opadd', 'sub': 'opsub', 'mul': 'opmul'}

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
    fully dispatched on for `ope`; the other six commands still accept but
    ignore them pending later phases (issues #22-#27).
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
        , choices = ['ope', 'com', '100', '99', 'aBc', 'squ', 'pi']
        , help = 'Type of formula to output (only "ope" is implemented; others render placeholder content)'
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
        , default = 10
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

    def set_min_max_value(value: int) -> list[int]:
        digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
        min_val, max_val = digits_list[value - 1]
        return [min_val, max_val]

    if args.a_value is not None:
        args.a_min, args.a_max = set_min_max_value(args.a_value)
    if args.b_value is not None:
        args.b_min, args.b_max = set_min_max_value(args.b_value)

    if args.rows < MIN_ROWS_OR_COLUMNS or args.columns < MIN_ROWS_OR_COLUMNS:
        failure(f"-r/--rows and -c/--columns must be at least {MIN_ROWS_OR_COLUMNS}.")

    if args.page < 1:
        failure("-p/--page must be at least 1.")

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
        layout: 'inline' (blocks joined with \\hspace on a single text line
            per row, used by horizontal-format problems) or 'tabular' (a
            LaTeX tabular grid with one block per cell, used by --vertical
            hissan blocks so multi-row blocks like xlop/longdivision output
            stay column-aligned).
    """
    blocks: list[str] = field(default_factory=list)
    columns: int = 1
    bottom_answer_tex: str | None = None
    layout: str = 'inline'


def build_preamble_tex(paper_size: str) -> str:
    geometry_option = PAPER_SIZE_TO_GEOMETRY_OPTION[paper_size.lower()]
    return (
        "\\documentclass[12pt]{article}\n"
        f"\\usepackage[{geometry_option},margin=15mm,top=20mm,bottom=20mm]{{geometry}}\n"
        "\\usepackage{longdivision}\n"
        "\\usepackage{xlop}\n"
        "\\usepackage{array}\n"
        "\\usepackage{fancyhdr}\n"
        "\\pagestyle{fancy}\n"
        "\\fancyhf{}\n"
        f"\\fancyfoot[L]{{{COPYRIGHT_STR}}}\n"
        "\\fancyfoot[R]{Page \\#\\thepage}\n"
        "\\renewcommand{\\headrulewidth}{0pt}\n"
        "\\renewcommand{\\footrulewidth}{0pt}\n"
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
    """Join blocks into text rows separated by \\hspace, one row per line."""
    row_lines = []
    for row_start in range(0, len(blocks), columns):
        row_blocks = blocks[row_start:row_start + columns]
        row_lines.append((f"\\hspace{{{BLOCK_GUTTER_CM}cm}}").join(row_blocks))
    return f"\\par\\vspace{{{ROW_VSPACE_EM}em}}\n".join(row_lines)


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
    for row_start in range(0, len(blocks), columns):
        row_blocks = blocks[row_start:row_start + columns]
        row_blocks += [''] * (columns - len(row_blocks))
        row_tex = ' & '.join(row_blocks)
        row_tabulars.append(f"\\begin{{tabular}}{{{column_spec}}}\n{row_tex}\n\\end{{tabular}}")
    return f"\\par\\vspace{{{ROW_VSPACE_EM}em}}\n".join(row_tabulars)


def build_page_tex(page: Page) -> str:
    """Render one Page's grid of blocks, plus header and optional bottom answer."""
    if page.layout == 'tabular':
        grid_tex = build_tabular_grid_tex(page.blocks, page.columns)
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
    """Retry with freshly-sampled operands until the result is positive."""
    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if a - b > 0:
            return a, b, a - b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    raise ValueError(
        "No subtraction pair with a positive result (a - b > 0) "
        "found in the given number ranges."
    )


def calc_mul(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    return a, b, a * b


def calc_div(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    """Retry with freshly-sampled operands until the division is exact."""
    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if b != 0 and a % b == 0:
            return a, b, a // b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
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
    result_tex = str(problem.c) if show_answer else '\\underline{\\hspace{1.5em}}'
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
    result_tex = str(problem.c) if show_answer else '\\underline{\\hspace{1.5em}}'
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
        return index_line + op_call_tex
    return (
        index_line
        + "\\begingroup\\opset{resultstyle=\\phantom,carrystyle=\\phantom,intermediarystyle=\\phantom}"
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


def build_placeholder_page(rows: int, columns: int, page_number: int, show_work: bool) -> Page:
    """
    Phase-1 placeholder content, still used for the six commands not yet
    implemented (com/100/99/aBc/squ/pi -- issues #22-#27). `ope` uses real
    problem data (build_ope_pages) since Phase 2 (issue #21).
    """
    start_index = (page_number - 1) * rows * columns + 1
    blocks = []
    for offset in range(rows * columns):
        index = start_index + offset
        blocks.append(f"{index}) \\_\\_\\_ = {index}" if show_work else f"{index}) \\_\\_\\_")
    return Page(blocks=blocks, columns=columns)


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


def build_placeholder_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page]]:
    """Phase-1 placeholder content for commands not yet implemented (issues #22-#27)."""
    blank_pages = [
        build_placeholder_page(ini.rows, ini.columns, page_number, show_work=False)
        for page_number in range(1, ini.page + 1)
    ]
    filled_pages = [
        build_placeholder_page(ini.rows, ini.columns, page_number, show_work=True)
        for page_number in range(1, ini.page + 1)
    ]
    if ini.with_bottom_answer:
        for page_number, blank_page in enumerate(blank_pages, start=1):
            start_index = (page_number - 1) * ini.rows * ini.columns + 1
            entries = " \\quad ".join(
                f"({i}) {i}" for i in range(start_index, start_index + ini.rows * ini.columns)
            )
            blank_page.bottom_answer_tex = entries
    return blank_pages, filled_pages


def main(ini: argparse.Namespace) -> None:
    if shutil.which('pdflatex') is None:
        failure(
            "pdflatex not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    pages_problems: list[list[OpeProblem]] | None = None
    if ini.command == 'ope':
        blank_pages, filled_pages, pages_problems = build_ope_pages(ini)
    else:
        blank_pages, filled_pages = build_placeholder_pages(ini)

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
        if pages_problems is not None:
            rows = build_ope_csv_rows(pages_problems)
        else:
            rows = [
                [page_number, index]
                for page_number, page in enumerate(blank_pages, start=1)
                for index in range(1, len(page.blocks) + 1)
            ]
        write_csv(rows, outfile_csv)

    print("export PDF")
    print("All done")


if __name__ == '__main__':
    main(_init())
