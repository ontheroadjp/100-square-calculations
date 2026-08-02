#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nuts_calc_tex.py -- Phase 1: common CLI/PDF foundation (issue #20).

A 100%-LaTeX-rendered, fully independent reimplementation of nuts_calc.py's
CLI surface (see the tracking issue #19). This file has zero code
dependency on nuts_calc.py: no imports, no shared modules -- the two are
meant to run side by side, each self-contained.

This phase builds the shared plumbing only: CLI argument parsing, page/PDF
layout in LaTeX, the pdflatex build pipeline, and CSV output. Per-command
problem generation and rendering (ope/com/100/99/aBc/squ/pi) is added in
later phases (issues #21-#27); until then, `main()` renders placeholder
content just to exercise the full pipeline end-to-end.

Requires a LaTeX distribution (`pdflatex`) on PATH. The `longdivision`
CTAN package (needed starting in Phase 2 for `ope --vertical -o div`) is
vendored into this repo under `vendor/texmf/` and located via TEXINPUTS,
so no manual TeX package installation is required beyond a base LaTeX
distribution (e.g. `texlive-latex-base`).
"""

import argparse
import csv
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field


MIN_ROWS_OR_COLUMNS = 1
BLOCK_GUTTER_CM = 1.0
ROW_VSPACE_EM = 2.0

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_TEXMF_DIR = os.path.join(SCRIPT_DIR, 'vendor', 'texmf')

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
    accepted here but not yet dispatched on -- that lands in later phases.
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
        , help = 'Type of formula to output (not yet dispatched on in Phase 1)'
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
    """
    blocks: list[str] = field(default_factory=list)
    columns: int = 1
    bottom_answer_tex: str | None = None


def build_preamble_tex(paper_size: str) -> str:
    geometry_option = PAPER_SIZE_TO_GEOMETRY_OPTION[paper_size.lower()]
    return (
        "\\documentclass[12pt]{article}\n"
        f"\\usepackage[{geometry_option},margin=15mm,top=20mm,bottom=20mm]{{geometry}}\n"
        "\\usepackage{longdivision}\n"
        "\\usepackage{xlop}\n"
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


def build_page_tex(page: Page) -> str:
    """Render one Page's grid of blocks, plus header and optional bottom answer."""
    row_lines = []
    for row_start in range(0, len(page.blocks), page.columns):
        row_blocks = page.blocks[row_start:row_start + page.columns]
        row_lines.append((f"\\hspace{{{BLOCK_GUTTER_CM}cm}}").join(row_blocks))
    grid_tex = f"\\par\\vspace{{{ROW_VSPACE_EM}em}}\n".join(row_lines)

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


def build_placeholder_page(rows: int, columns: int, page_number: int, show_work: bool) -> Page:
    """
    Phase-1 placeholder content, to be replaced by real per-command
    rendering starting in Phase 2 (issue #21 onward). Exercises the full
    pipeline (grid layout, blank/filled/merge, CSV) without any real
    problem data.
    """
    start_index = (page_number - 1) * rows * columns + 1
    blocks = []
    for offset in range(rows * columns):
        index = start_index + offset
        blocks.append(f"{index}) \\_\\_\\_ = {index}" if show_work else f"{index}) \\_\\_\\_")
    return Page(blocks=blocks, columns=columns)


def main(ini: argparse.Namespace) -> None:
    if shutil.which('pdflatex') is None:
        failure(
            "pdflatex not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

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
