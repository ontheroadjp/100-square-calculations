#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Script: 100masu.py
# Description: This Python script generates various types of mathematical
#              practice worksheets (e.g., 100-square calculations, basic
#              arithmetic operations, complements, multiplication tables)
#              and outputs them as PDF files. It provides extensive
#              customization options via command-line arguments for problem
#              types, number ranges, paper sizes, and output formats.
#
# Usage: python 100masu.py <paper_size> <command> [options]
#
# Arguments:
#   <paper_size>: Specifies the paper size for the output PDF (e.g., A3, A4, B5, a4l).
#   <command>: Defines the type of mathematical problem to generate.
#              Supported commands include:
#              - 'ope': Basic arithmetic operations (add, sub, mul, div, mix).
#              - 'com': Complements (e.g., numbers that add up to 100).
#              - '100': 100-square calculation tables.
#              - '99': Multiplication tables (kuku).
#              - 'aBc': Specific mental arithmetic problems (e.g., a*1000 + b*100 + c*10 + d).
#              - 'squ': Square numbers.
#              - 'pi': Multiplication by Pi (e.g., a * 3.14).
#
# Options:
#   -a, --a-value: Number of digits in the first term.
#   -b, --b-value: Number of digits in the second term.
#   --a-min, --a-max: Minimum/maximum value for the first term.
#   --b-min, --b-max: Minimum/maximum value for the second term.
#   -o, --operator: Types of operations to include (add, sub, mul, div, mix).
#   --descend, --reverse, --shuffle: Ordering options for multiplication tables.
#   --intermediate: Write an intermediate formula (for multiplication).
#   -r, --rows: Number of question rows per page.
#   -c, --columns: Number of question columns per page.
#   -ww, --with-bottom-answer: Flag to include answers at the bottom of the page.
#   -p, --page: Number of pages to generate.
#   -m, --merge: Flag to merge answer files.
#   --csv: Flag to output raw data to CSV.
#   --out-file: Output PDF file path (default: 'result.pdf').
#   --debug: Enable debug mode (shows frame boundaries, etc.).
#
# Processing Flow:
# 1.  **Argument Parsing**: Command-line arguments are parsed to configure the generation process.
# 2.  **PDF Document Setup**: Initializes PDF document templates, page sizes, margins, and frames using ReportLab.
# 3.  **Problem Data Generation**: Based on the specified 'command' and options,
#     functions like `get_operation_data`, `get_complement_data`, `get_fixed_format_data`,
#     and `get_aBc_data` generate the mathematical problems.
# 4.  **Layout and Styling**: The generated problem data is formatted into tables
#     and styled according to the specified paper size and other display options.
# 5.  **PDF Generation**: The formatted content is built into one or more PDF files.
#     Optional CSV output is also handled.
#
# Dependencies:
# -   Python 3
# -   ReportLab library (`reportlab`)
#
# Output:
# -   PDF files containing the generated worksheets.
# -   Optionally, CSV files with raw problem data.
#
# Version: 0.1.0 (based on factory.sh, actual version might differ)
# Last Updated: September 13, 2025
#
#
import sys
import os
import argparse
import random
import csv
#import copy
#import math
#from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, A3, landscape
from reportlab.platypus import BaseDocTemplate, PageTemplate
from reportlab.platypus import Frame, FrameBreak, PageBreak
from reportlab.platypus import Table, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors


SINGLE_DIGIT_MAX = 9
VERTICAL_UNSUPPORTED_OPERATORS = {'div', 'mix'}
VERTICAL_BLOCK_ROWS = 3
VERTICAL_INDEX_COLUMN_RATIO = 0.28
VERTICAL_BLOCK_HEIGHT_RATIO = 0.85


def failure(e):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    print(str(lineno) + ": " + str(type(e)))
    print(str(lineno) + ": " + str(e))
    exit(-1)


def _init():
    """
    Initialize argument parser and parse command line arguments.

    Returns:
        args: argparse object
            Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s A4 | B5",
        description = """
            This script outputs a calculation practice printout of
            the four arithmetic operations and saves it in PDF format.
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
#        , choices = ['ope', 'mul-intermediate', 'com', '100', '99', 'aBc', 'squ', 'pi']
        , choices = ['ope', 'com', '100', '99', 'aBc', 'squ', 'pi']
        , help = 'Type of formula to output'
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
        , help = 'Output "ope" problems in vertical (column / written-calculation, hissan) format'
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
        , default = '1'
        , help = 'Number of pages included in the output file'
    )
    parser.add_argument('-m', '--merge'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to merge answers file'
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
        , help = 'Number of pages included in the output file'
    )
    args = parser.parse_args()

    def set_min_max_value(value):
        digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
        min_val, max_val = digits_list[value - 1]
        return [min_val, max_val]

#    if args.command == 'ope' or args.command == 'mul-intermediate':
    if args.command == 'ope' or args.intermediate:
        if args.a_value is not None:
            args.a_min, args.a_max = set_min_max_value(args.a_value)
        if args.b_value is not None:
            args.b_min, args.b_max = set_min_max_value(args.b_value)
    elif args.command == 'com' \
            or args.command == '99' \
            or args.command == 'squ' \
            or args.command == 'pi':
        if args.a_value is None:
            print(f"-a option must be set.")
            exit()
    elif args.command == '100':
        if args.a_value is None:
            args.a_value = 1
            args.a_min, args.a_max = set_min_max_value(args.a_value)
        if args.b_value is None:
            args.b_value = 1
            args.b_min, args.b_max = set_min_max_value(args.b_value)
        if args.a_value > 3 or args.b_value > 3:
            print(f"bad argument: -a or -b")
            print('They must be less than 3.')
            exit()

    if args.vertical:
        if args.command != 'ope':
            print("--vertical is only supported for the 'ope' command.")
            exit(1)
        if args.intermediate:
            print("--vertical cannot be combined with --intermediate.")
            exit(1)
        unsupported = VERTICAL_UNSUPPORTED_OPERATORS.intersection(args.operator)
        if unsupported:
            print(f"--vertical does not support operator(s): {', '.join(sorted(unsupported))}.")
            exit(1)
        if 'mul' in args.operator and args.b_max > SINGLE_DIGIT_MAX:
            print("--vertical only supports 'mul' when the second operand is a single digit (use -b 1 or --b-max <= 9).")
            exit(1)

    return args


def add_vertical_frame_set(frames, start_x, start_y, region_w, region_h, frame_amount, w_ratio, show):
    table_frame_w = region_w / frame_amount
    table_frame_h = region_h

    table_frame_w_list = []
    [table_frame_w_list.append(table_frame_w) for i in range(len(w_ratio))]

    def calc_table_frame_width(data, ratio):
        total_ratio = 0
        total_data = 0
        value = []
        for i in ratio:
            total_ratio += i
        for i in data:
            total_data += i
        for i, v in enumerate(data):
            value.append(total_data * (ratio[i] / total_ratio))
        return value

    table_frame_calc_w = calc_table_frame_width(table_frame_w_list, w_ratio)
    tmp = calc_table_frame_width(table_frame_w_list, w_ratio)
    offset = 0
    for i in range(frame_amount):
        x = start_x + offset
        y = start_y
        if i > (len(w_ratio) - 1):
            tmp.extend(tmp)
        w = tmp[i]
        h = region_h
        frames.append(Frame(x, y, w, h
            , leftPadding=0, bottomPadding=0
            , rightPadding=0, topPadding=0
            , showBoundary = show
        ))
        offset += w
    return table_frame_calc_w


def get_operation_data(
        nums_a, nums_b, operators=['add'], order=10, print_index = 1,
        intermediate = False
    ):
    """
    Create the four operations from num_a and num_b.

    Args:
        nums_a: list
            List of seed numbers for using develop the four operations
        nums_b: list
            List of seed numbers for using develop the forur operations
        operators: list
            List of operator symbol
        order: int
            Number of creating questions
        print_index: int
            begining number of question

    Returns:
        the four operations: tuple
            List of the four operation elements
    """
    data_index = []
    vals_a = []
    operator_mark = []
    vals_b = []
    equal_marks = []
    vals_c = []
    vals_aabb = []
    print_style = {'add':'+', 'sub':'-', 'mul':'×', 'div':'÷'}
    if operators.count('mix') > 0:
        operators = ['add', 'sub', 'mul', 'div']

    def calc_add(a, b):
        c = a + b
        return (a, b, c)

    def calc_sub(a, b):
        while True:
            # Make sure the answer is not a negative number.
            if a - b > 0:
                c = a - b
                return (a, b, c)
            a = random.choice(nums_a)
            b = random.choice(nums_b)

    def calc_mul(a, b):
        c = a * b
        return (a, b, c)

    def calc_div(a, b):
        while True:
            # Only if not divisible by zero and divisible by
            if b != 0 and a % b == 0:
                c = a // b
                return (a, b, c)
            a = random.choice(nums_a)
            b = random.choice(nums_b)

    for _ in range(order):
        a = random.choice(nums_a)
        b = random.choice(nums_b)
        random.shuffle(operators)
        operator = random.choice(operators)
        if operator == 'add':
#            c = a + b
            a, b, c = calc_add(a, b)
        elif operator == 'sub':
#            while True:
#                # Make sure the answer is not a negative number.
#                if a - b > 0:
#                    c = a - b
#                    break
#                a = random.choice(nums_a)
#                b = random.choice(nums_b)
            a, b, c = calc_sub(a, b)
        elif operator == 'mul':
#        elif operator == 'mul' or operator == 'mul-intermediate':
#            c = a * b
            a, b, c = calc_mul(a, b)
            if intermediate:
                single_a = a // 10
                single_b = a % 10
                single_c = b // 10
                single_d = b % 10
                aa = '00' + str(single_a * single_d)
                bb = '00' + str(single_b * single_d)
                aabb = aa[-2:] + bb[-2:]
#                print(str(a) + '×' + str(b) + '=>' + str(aabb) + '=>' + str(c))
        elif operator == 'div':
#            while True:
#                # Only if not divisible by zero and divisible by
#                if b != 0 and a % b == 0:
#                    c = a // b
#                    break
#                a = random.choice(nums_a)
#                b = random.choice(nums_b)
            a, b, c = calc_div(a, b)

        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        vals_a.append([str(a)])
        operator_mark.append([str(print_style[operator[:3]])])
        vals_b.append([str(b)])
        vals_c.append([str(c)])
        if intermediate:
            equal_marks.append(['=>'])
            vals_aabb.append([str(aabb)])
        else:
            equal_marks.append(['='])

        print_index += 1

    if intermediate:
        return (data_index, vals_a, operator_mark, vals_b, equal_marks, vals_aabb, equal_marks, vals_c)
    else:
        return (data_index, vals_a, operator_mark, vals_b, equal_marks, vals_c)


def get_complement_data(nums_a, target=100, order=10, print_index=1):
    """
    Create complement from target of nums_s

    Args:
        nums_a: list
            List of seed numbers for using develop complemention
        target: int
            Complement target number
#        include_number: bool, optional
#            Whether to include the number before the complemention (default is False)

    Returns:
        complements: list
            List of the four operations in the format like "a + b = c" or "c = a + b"
            [0] = no answer, [1] = with answer
    """
    data_index = []
    vals_a = []
    equal_marks = []
    vals_c = []
#    count = 1
    for _ in range(order):
        a = random.choice(nums_a)
        c = target - a
        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        vals_a.append([a])
        equal_marks.append(['=>'])
        vals_c.append([c])
        print_index += 1
#        count += 1
    return(data_index, vals_a, equal_marks, vals_c)


def get_fixed_format_data(mode, start_num=1, order=10, print_index=1,
                            descend=False, is_reverse=False, is_shuffle=False):
    """
    Create the square numbers operations

    Args:
        num_min: int
            Create the 99 for
        num_max: int
            Number of creating 99 questions
        print_index: int
            begining number of question
        descend: boolean
            Output in descending order of 99
        is_shuffle: boolean
            Disjointed output of the order of the 99

    Returns:
        the 99 operations: tuple
            List of the four operation elements
    """
    data_index = []
    vals_a = []
    operator_marks = []
    vals_b = []
    equal_marks = []
    vals_c = []

    if mode == '99':
        num_list = [i for i in range(order)]
    else:
        num_list = [(start_num + i) for i in range(order)]

    if descend:
        num_list.reverse()
    if is_shuffle:
        random.shuffle(num_list)

    for index in range(order):
        if mode == '99':
            a = start_num
            b = num_list[index] + 1
            c = a * b
        elif mode == 'squ':
            a = num_list[index]
            b = a
            c = a * a
        elif mode == 'pi':
            a = num_list[index]
            b = 3.14
            c = a * b

        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        vals_a.append([a])
        operator_marks.append(['×'])
        vals_b.append([b])
        equal_marks.append(['='])
        vals_c.append([c])
        print_index += 1

        if not mode == '99':
            start_num += 1
    if is_reverse is True:
        return (data_index, vals_c, equal_marks, vals_a, operator_marks, vals_b)
    return (data_index, vals_a, operator_marks, vals_b, equal_marks, vals_c)


def get_aBc_data(order = 10, print_index = 1):
    """
    Create the aBc statement

    Args:
        order: int
            Create number of statement
        print_index: int
            statement No
    Returns:
        the aBc statements: tuple
            List of the aBc statements
    """
    seed_nums = [a for a in range(0, 10)]

    vals_a = []
    equal_marks = []
    vals_c = []
    data_index = []
    for i in range(order):
        a = random.choice(seed_nums)
        b = random.choice(seed_nums)
        c = random.choice(seed_nums)
        d = random.choice(seed_nums)

        abcd = a * 1000 + b * 100 + c * 10 + d
        ab = (a * 10 + b) * 10
        cd = c * 10 + d
        a_d = ab + cd
        if len(str(abcd)) == 3:
            abcd = '0' + str(abcd)
            vals_a.append([abcd])
        else:
            vals_a.append([str(abcd)])
        equal_marks.append(['=>'])
        vals_c.append([str(a_d)])
        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        print_index += 1
    return (data_index, vals_a, equal_marks, vals_c)


def add_header_index(contents, data, width, height, grid_color):
    """
    Add header index table. This table has one column and one row.

    Args:
        contents: list
            Container of the header index content
        data: list
            Header index content
        width: int
            Region width of the header index table
        height: int
            Region height of the header index table
        grid_color: str
            Grid color of the header index table
    Returns:
        Not available
    """
    header_index_tbl = Table( [data]
        , colWidths = [width] * 2
        , rowHeights = [height] * 1
    )
    header_index_tbl.setStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, grid_color),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 24),
    ])
    contents.append(header_index_tbl)
    contents.append(FrameBreak())

def get_vertical_contents_raw_dataset(command, data_elements, rows, columns):
    """
    Return the vertical contents raw data.

    Args:
        command: str
            This is from an argument of this script
        data_elements: list
            Seed for creating contents data
        rows: int
            Number of row of a table
        columns: int
            Number of column of a table
    Returns:
        dataset: list
            All of the raw data created
    """
    order = rows * 1
    dataset = []
    for column_index in range(columns):
        print_index = 1 + (rows * column_index)
        if command == '99' or command == 'squ' or command == 'pi':
            mode, start_num, descend, is_reverse, is_shuffle = data_elements
            data = get_fixed_format_data(
                mode, start_num, order, print_index
                , descend, is_reverse, is_shuffle
            )
        elif command == 'ope':
            nums_a, nums_b, operator, intermediate = data_elements
            if intermediate:
                operator = ['mul']
            data = get_operation_data(
                nums_a, nums_b, operator, order, print_index, intermediate
            )
#        elif command == 'mul-intermediate':
#            nums_a, nums_b, operator = data_elements
#            data = get_operation_data(
#                nums_a, nums_b, operator, order, print_index
#            )
        elif command == 'com':
            target, random_nums = data_elements
            data = get_complement_data(
                random_nums, target, order, print_index
            )
        elif command == 'aBc':
            data = get_aBc_data(order, print_index)

#        elif command == 'mix':
#            nums_a = 2
#            nums_b = 1
#            operator = 'mul'
#            order = 4
#            data = get_operation_data(
#                nums_a, nums_b, operator, order, print_index
#            )

        dataset.append(data)
    return dataset


def get_vertical_contents(dataset, row_heights, col_widths
#    ,align ,valign ,font_size ,top_padding ,left_padding ,grid_color ,text_color):
    ,align ,valign ,font_size ,top_padding ,left_padding ,grid_color):

    vertical_contents = []
    for data in dataset:
        table_set = []
        for data_index in range(len(data)):
            top_table = Table(data[data_index]
                , rowHeights = row_heights
                , colWidths = col_widths[data_index]
            )
            top_table.setStyle([
                ('ALIGN', (0, 0), (-1, -1), align[data_index])
                , ('VALIGN', (0, 0), (-1, -1), valign[data_index])
                , ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
                , ('FONTSIZE', (0, 0), (-1, -1), font_size[data_index])
#                , ('TEXTCOLOR', (0, 0), (-1, -1), text_color[data_index])
                , ('TOPPADDING', (0, 0), (-1, -1), top_padding[data_index])
                , ('LEFTPADDING', (0, 0), (-1, -1), left_padding[data_index])
                , ('GRID', (0, 0), (-1, -1), 0, grid_color)
#                , ('INNERGRID', (0, 0), (-1, -1), 0, grid_color)
#                , ('BOX', (0, 0), (-1, -1), 0, grid_color)
#                , ('INNERGRID', (0, 0), (-1, -1), 0, grid_color)
#                , ('OUTLINE', (0, 0), (-1, -1), 0, grid_color)
            ])
            table_set.append(top_table)
        vertical_contents.append(table_set)
    return vertical_contents


def pad_digits_to_width(value: str, width: int) -> list[str]:
    """
    Right-align a numeric string into a fixed-width list of single-character cells.

    Args:
        value: str
            The numeric string to align (e.g. "45").
        width: int
            Total number of digit columns to fill.

    Returns:
        cells: list[str]
            `width` cells, blank-padded on the left, one digit per cell.
    """
    padded = value.rjust(width)
    return [char if char != ' ' else '' for char in padded]


def get_vertical_digit_width(a_max: int, b_max: int, operators: list[str]) -> int:
    """
    Compute the digit column width needed to fit operands and results
    for the given operators in vertical (written-calculation) format.

    Args:
        a_max: int
            Exclusive upper bound of the first operand's range.
        b_max: int
            Exclusive upper bound of the second operand's range.
        operators: list
            Operators to be rendered (subset of 'add', 'sub', 'mul').

    Returns:
        width: int
            Number of digit columns required.
    """
    candidates = [a_max, b_max]
    if 'add' in operators:
        candidates.append(a_max + b_max)
    if 'sub' in operators:
        candidates.append(a_max)
    if 'mul' in operators:
        candidates.append(a_max * b_max)
    return len(str(max(candidates)))


def get_vertical_calc_block(
        index_str: str, a_str: str, operator_symbol: str, b_str: str, c_str: str,
        digit_width: int, index_col_width: float, digit_col_width: float,
        slot_height: float, font_size: int, grid_color
    ):
    """
    Build one vertical (written-calculation / hissan) problem block.

    Layout is 3 rows x (1 + digit_width) columns:
        row 0: [index]     [digits of a, right-aligned]
        row 1: [operator]  [digits of b, right-aligned]   (a line is drawn below this row)
        row 2: [blank]     [digits of c, right-aligned]   (c_str == '' leaves the answer blank)

    Args:
        index_str: str
            Problem number label (e.g. "3)").
        a_str: str
            First operand as a string.
        operator_symbol: str
            Operator glyph (e.g. '+', '-', '×').
        b_str: str
            Second operand as a string.
        c_str: str
            Answer as a string, or '' to leave the answer row blank.
        digit_width: int
            Number of digit columns (shared across all blocks on the page for alignment).
        index_col_width: float
            Width of the leading index/operator column.
        digit_col_width: float
            Width of each digit column.
        slot_height: float
            Total height available for the 3-row block.
        font_size: int
            Font size for the block's text.
        grid_color:
            reportlab color used for the (usually invisible) debug grid.

    Returns:
        table: reportlab.platypus.Table
    """
    data = [
        [index_str] + pad_digits_to_width(a_str, digit_width),
        [operator_symbol] + pad_digits_to_width(b_str, digit_width),
        [''] + (pad_digits_to_width(c_str, digit_width) if c_str else [''] * digit_width),
    ]
    col_widths = [index_col_width] + [digit_col_width] * digit_width
    row_heights = [(slot_height * VERTICAL_BLOCK_HEIGHT_RATIO) / VERTICAL_BLOCK_ROWS] * VERTICAL_BLOCK_ROWS

    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
    table.setStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
        ('GRID', (0, 0), (-1, -1), 0, grid_color),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ])
    return table


def get_bottom_results(dataset, tbl2_w, tbl2_h, grid_color):
    cumulative_index = 1
    bottom_results = []
    bottom_result_line = []
    for data in dataset:
        for data_index in range(len(data)):
            if data_index == (len(data) - 1):
                for val in data[data_index]:
                    bottom_result_line.append(f"({cumulative_index})")
                    bottom_result_line.append(val[0])
                    cumulative_index += 1
                    if len(bottom_result_line) > 18:
                        bottom_results.append(bottom_result_line)
                        bottom_result_line = []
    if len(bottom_result_line):
        bottom_results.append(bottom_result_line)

    row_heights = [tbl2_h / len(bottom_results)] * len(bottom_results)
    col_widths = [tbl2_w / 20] * 20
    table = Table(bottom_results
        , rowHeights = row_heights
        , colWidths = col_widths
    )
    table.setStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8)
        , ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        , ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        , ('GRID', (0, 0), (-1, -1), 0, grid_color)
    ])
    return table


def addPageNumber(canvas, doc):
    """
    Add the page number
    # https://docs.reportlab.com/reportlab/userguide/ch2_graphics/
    """
    paper_w, paper_h = doc.pagesize

#    print(canvas.getAvailableFonts())

    # Line settings
#    canvas.setLineWidth(5)
#    canvas.setLineCap(mode)
#    canvas.setLineJoin(mode)
#    canvas.setMiterLimit(limit)
#    canvas.setDash(self, array=[], phase=0)
    canvas.setLineWidth(0.5)
    canvas.setDash([2, 2])

    # Draw lines (virtual page sepalater)
    if paper_h == 1190.5511811023623:   # A3
        canvas.line(paper_w / 2, 30, paper_w / 2, paper_h - 30)
        canvas.line(30, paper_h / 2, paper_w - 30, paper_h / 2)
    elif paper_h == 595.2755905511812:  # landscape(A4)
        canvas.line(paper_w / 2, 30, paper_w / 2, paper_h - 30)

    # Draw Page Number
    page_num = canvas.getPageNumber()
    canvas.setFont('Helvetica', 8)
    page_no = "Page #%s" % page_num
    canvas.drawRightString(paper_w - 25, 25, page_no)

    # Draw Copyrights
    cr = 'Copyright(c) 2024 Nuts Education'
    canvas.drawString(25, 25, cr)


def main(ini):
    """
    Main routine to generate the table and output as PDF.

    Args:
        args: argparse object
            Parsed arguments.
    """
#    print(f"{ini.a_value=}")
#    print(f"{ini.b_value=}")
#    print(f"{ini.a_min=}")
#    print(f"{ini.a_max=}")
#    print(f"{ini.b_min=}")
#    print(f"{ini.b_max=}")

    HEADER_STR = 'Nuts Education'
    TITLE_STR = '100 square calculations'
    SUB_TITLE_STR = 'for Mental Arithmetic'
    DATE_LABEL = 'Date: '
    TIME_LABEL = 'Time: '
    AUTHOR = 'Nuts Education'
    #SUBJECT = 'Adding metadata to pdf via reportlab'
    SUBJECT = ''

    if ini.paper_size.lower() == 'a3':
        paper_width, paper_height = A3
    elif ini.paper_size.lower() == 'a4':
        paper_width, paper_height = A4
    elif ini.paper_size.lower() == 'a4l':
        paper_width, paper_height = landscape(A4)
    elif ini.paper_size.lower() == 'b5':
        paper_width, paper_height = B5

    margin_top = 20 * mm
    margin_bottom = 20 * mm
    margin_left = 15 * mm
    margin_right = 15 * mm

    if ini.paper_size.lower() == 'a4':
        header_font_size = 14
        title_font_size = 24
        sub_title_font_size = 10
        date_time_font_size = 10
    elif ini.paper_size.lower() == 'b5' \
            or ini.paper_size.lower() == 'a4l' \
            or ini.paper_size.lower() == 'a3':
        header_font_size = 12
        title_font_size = 18
        sub_title_font_size = 8
        date_time_font_size = 8

    is_vertical_ope = ini.command == 'ope' and ini.vertical
    if is_vertical_ope:
        vertical_digit_width = get_vertical_digit_width(ini.a_max, ini.b_max, ini.operator)
        vertical_font_size = 16 if ini.paper_size.lower() == 'a4' else 11

    try:
        # Create Document (PDF)
        OUTFILE_NAME = ini.out_file
        OUTFILE_NAME_READ = ini.out_file.rstrip('.pdf') + '_read.pdf'
        OUTFILE_NAME_CSV = ini.out_file.rstrip('.pdf') + '.csv'

        docs = [
            BaseDocTemplate(
                OUTFILE_NAME
                , topMargin = margin_top
                , leftMargin = margin_left
                , rightMargin = margin_right
                , bottomMargin = margin_bottom
                , pagesize = (paper_width, paper_height)
                , title = TITLE_STR
                , author = AUTHOR
                , subject = SUBJECT
                , creator = AUTHOR
                , producer = AUTHOR
            )
        ]
        if ini.merge is False:
            docs.append(BaseDocTemplate(
                OUTFILE_NAME_READ
                , topMargin = margin_top
                , leftMargin = margin_left
                , rightMargin = margin_right
                , bottomMargin = margin_bottom
                , pagesize = (paper_width, paper_height)
                , title = TITLE_STR
                , author = AUTHOR
                , subject = SUBJECT
                , creator = AUTHOR
                , producer = AUTHOR
            ))

        if os.path.isfile(f"./{OUTFILE_NAME}"):
            os.remove(f"./{OUTFILE_NAME}")
        if os.path.isfile(f"./{OUTFILE_NAME_READ}"):
            os.remove(f"./{OUTFILE_NAME_READ}")

#        print(f"{paper_width=}")
#        print(f"{paper_height=}")
#        print('-------------------------')
#        print(297 * mm) # A3
#        print(420 * mm) # A3
#        print(210 * mm) # A4
#        print(297 * mm) # A4
#        print(182 * mm) # B5
#        print(257 * mm) # B5
#        print('-------------------------')

        # Virtual Page
        page_split = 1
        vp_w, vp_h = [paper_width, paper_height]
        reference_points = [(0, 0)]
        if ini.paper_size.lower() == 'a4l':
            page_split = 2
            vp_w, vp_h = [paper_width / 2, paper_height]
            reference_points = [(0, 0) , (paper_width / 2, 0)]
        if ini.paper_size.lower() == 'a3':
            page_split = 4
            vp_w, vp_h = [paper_width / 2, paper_height / 2]
            reference_points = (
                (0, paper_height / 2)
                ,(paper_width / 2, paper_height / 2)
                ,(0, 0), (paper_width / 2, 0)
            )

        # 0: normal, 1: read
        frames = [[],[]]
#        frames = [[]] * len(docs)

        def get_frame_ratio(command):
            if command == 'com' or command == 'aBc':
                w_ratio = [1, 1.5, 0.6, 1.5]
            elif ini.intermediate:
                w_ratio = [2, 2, 1.5, 1.5, 1.5, 4.2, 1.5, 4.2]
            else:
                w_ratio = [4.0, 3.2, 1.5, 2.5, 1.5, 3.2]
            return w_ratio

        for index in range(page_split):
            offset_x, offset_y = reference_points[index]

            # Header frame
            header_region_w = vp_w - margin_left - margin_right
            header_region_h = 40 * mm
            header_region_x = offset_x + margin_left
            header_region_y = offset_y + vp_h - margin_top - header_region_h

            x = header_region_x
            y = header_region_y
            w = header_region_w
            h = header_region_h
            for i in range(len(frames)):
                frames[i].append(Frame(x, y, w, h
                    , leftPadding = 0, bottomPadding = 0
                    , rightPadding = 0, topPadding = 0
                    , showBoundary = ini.debug
                ))

            # Index Frame
            header_index_frame_w = 20 * mm
            header_index_frame_h = 20 * mm
            x = header_region_x + header_region_w - header_index_frame_w
            y = header_region_y + header_region_h - header_index_frame_h
            w = header_index_frame_w
            h = header_index_frame_h
            for i in range(len(frames)):
                frames[i].append(Frame(x, y, w, h
                    , leftPadding = 0, bottomPadding = 0
                    , rightPadding = 0, topPadding = 0
                    , showBoundary = ini.debug
                ))

            # Body Region
            body_region_w = header_region_w
            body_region_h = vp_h - margin_top - header_region_h - margin_bottom
            body_region_x = header_region_x
            body_region_y = header_region_y - body_region_h

            # Bottom Body Region
            bottom_body_region_w = body_region_w
            bottom_body_region_h = 0 * mm
            if ini.with_bottom_answer:
                bottom_body_region_h = 25 * mm

            # Top Body Region
            top_body_region_w = body_region_w
            top_body_region_h = body_region_h - bottom_body_region_h
            top_body_region_x = body_region_x
            top_body_region_y = header_region_y - top_body_region_h


            table_frame_calc_w = []
            if is_vertical_ope:
                x = top_body_region_x
                y = top_body_region_y
                w = top_body_region_w
                h = top_body_region_h
                frame_amount = ini.columns
                w_ratio = [1] * ini.columns
                for i in range(len(frames)):
                    table_frame_calc_w = add_vertical_frame_set(
                        frames[i], x, y, w, h, frame_amount, w_ratio, ini.debug
                    )
            elif ini.command == 'ope' \
                    or ini.command == '99' \
                    or ini.command == 'squ' \
                    or ini.command == 'pi' \
                    or ini.command == 'com' \
                    or ini.command == 'aBc':
#                    or ini.command == 'aBc' \
#                    or ini.command == 'mul-intermediate':
                x = top_body_region_x
                y = top_body_region_y
                w = top_body_region_w
                h = top_body_region_h
                w_ratio = get_frame_ratio(ini.command)
                frame_amount = ini.columns * len(w_ratio)
                for i in range(len(frames)):
                    table_frame_calc_w = add_vertical_frame_set(
                        frames[i], x, y, w, h, frame_amount, w_ratio, ini.debug
                    )
            elif ini.command == '100':
                x = body_region_x
                y = body_region_y
                w = body_region_w
                h = body_region_h
                for i in range(len(frames)):
                    frames[i].append(Frame(x, y, w, h
                        , leftPadding = 0, bottomPadding = 0
                        , rightPadding = 0, topPadding = 0
                        , showBoundary = ini.debug
                    ))
            # Table 2 frame
            tbl2_w = body_region_w
            tbl2_h = bottom_body_region_h
            tbl2_x = header_region_x
            tbl2_y = header_region_y - body_region_h
            for i in range(len(frames)):
                frames[i].append(Frame(tbl2_x, tbl2_y, tbl2_w, tbl2_h
                    , leftPadding=0, bottomPadding=0
                    , rightPadding=0, topPadding=0
                    , showBoundary = ini.debug
                ))

#        pt = PageTemplate("frames", frames=frames
#                , onPage=addPageNumber, onPageEnd=addPageNumber)
        for i in range(len(docs)):
            pt = PageTemplate("frames", frames=frames[i], onPageEnd=addPageNumber)
            docs[i].addPageTemplates(pt)

        # 0: normal, 1: read
        contents = [[], []]
#        contents = [[]] * len(docs)

        # Header
        header = Paragraph(f'<b>{HEADER_STR}</b>', ParagraphStyle(
            name='Header', leftIndent=0, fontName='Courier-Bold'
            , fontSize=header_font_size
        ))
        # Title
        title = Paragraph(f'<b>{TITLE_STR}</b>', ParagraphStyle(
            name='Title', fontName='Helvetica-Bold', fontSize=title_font_size
        ))
        # Sub title
        sub_title = Paragraph(f'<b>{SUB_TITLE_STR}</b>', ParagraphStyle(
            name='SubTitle', leftIndent=350, fontName='Helvetica'
            , fontSize=sub_title_font_size
        ))
        # Date and Time
        date_time = Table([[f"Date: {'_' * 15}", f"Time: {'_' * 15}"]],
            colWidths = [header_region_w / 2] * 2
        )
        date_time.setStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ])

        headers = [
            header, Spacer(1, 0)
            , title, Spacer(1, 60)
#            , sub_title, Spacer(1, 10)
            , date_time
        ]

        # ------------------------------------------------
        # ini.command == 100 # 100 square
        # ini.command == 'ope' # operation
        # ini.command == 'com' # complement
        # ------------------------------------------------

        # Generic Dimentions (for Top & Bottom table layout)
#        table_space = 0 if ini.with_bottom_answer else -20
#        row_heights = [(top_body_region_h - table_space) / ini.rows] * ini.rows

        row_heights = [(top_body_region_h - 0) / ini.rows] * ini.rows
        if ini.with_bottom_answer:
            row_heights = [(top_body_region_h - 20) / ini.rows] * ini.rows

        # Generic Table Style (for 6 units / column)
        align = ['RIGHT', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'LEFT', 'CENTER', 'CENTER']
        valign = ['MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE']
#        text_color = ['black', 'black', 'black', 'black', 'black', 'black', 'black', 'black']
        if ini.paper_size.lower() == 'a4':
            font_size = (10, 16, 16, 16, 16, 16, 16, 16)
        if ini.paper_size.lower() == 'b5' \
                or ini.paper_size.lower() == 'a4l' \
                or ini.paper_size.lower() == 'a3':
            font_size = (7, 11, 11, 11, 11, 11, 11, 11)
        grid_color = colors.HexColor('#00FFFFFF') if not ini.debug else colors.blue
        top_padding = (5, 0, -2, 0, -2, 0, 0, 0)
        left_padding = (4, 4, 2, 4, 4, 4, 4, 4)

        # Generic Table Style (for 4 units / column)
        if ini.command == 'com' or ini.command == 'aBc':
            align[3] = 'LEFT'
#            text_color[3] = 'white'
            font_size = (7, 11, 9, 11)

        if ini.intermediate:
            align[5] = 'CENTER'
            font_size = (7, 11, 11, 11, 9, 11, 9, 11)
            top_padding = (5, 0, -2, 0, 1, 0, 1, 0)

#        # for debug
#        if ini.debug:
#            text_color[-1] = 'black'
#            text_color[3] = 'black'

        # Document Development
        csv_data = []
        virtual_page_counter = 1
        next_content = None
        if not ini.command == '100':
            for page_index in range(ini.page):
                for _ in range(page_split):
                    # Header & Header Index
                    for i in range(len(contents)):
                        contents[i].extend(headers)
                        contents[i].append(FrameBreak())
                        add_header_index(contents[i], [f"# {virtual_page_counter}"],
                            header_index_frame_w, header_index_frame_h, grid_color
                        )

                    # Create Data Elements
                    data_elements = ()
                    if ini.command == '99' or ini.command == 'squ' \
                            or ini.command == 'pi':
                        data_elements = (
                            ini.command, ini.a_value
                            , ini.descend, ini.reverse, ini.shuffle
                        )
#                    elif ini.command == 'ope' or ini.command == 'mul-intermediate':
                    elif ini.command == 'ope':
                        if ini.a_min is not ini.a_max:
                            seed = [i for i in range(ini.a_min, ini.a_max)]
                            nums_a = random.sample(seed, len(seed))
                        else:
                            nums_a = [ini.a_min]
                        if ini.b_min is not ini.b_max:
                            seed = [i for i in range(ini.b_min, ini.b_max)]
                            nums_b = random.sample(seed, len(seed))
                        else:
                            nums_b = [ini.b_min]

#                        if ini.command == 'ope':
#                            operator = ini.operator
#                        elif ini.intermediate:
#                            operator = ['mul-intermediate']

                        operator = ini.operator
                        data_elements = (nums_a, nums_b, operator, ini.intermediate)
                    elif ini.command == 'com':
                        # Data elements
                        target = ini.a_value
                        seed = [i for i in range(1, target - 1)]
                        random_nums = random.sample(seed, len(seed))
                        data_elements = (target, random_nums)
                    elif ini.command == 'aBc':
                        data_elements = ()

                    dataset = get_vertical_contents_raw_dataset(
                        ini.command, data_elements, ini.rows, ini.columns
                    )

                    # for CSV
                    if ini.csv or ini.debug:
                        for i in range(len(dataset)):
                            for row in range(len(dataset[i][0])):
                                csv_line = []
                                csv_line.append(page_index)
                                csv_line.append(virtual_page_counter)
                                for el in range(len(dataset[i])):
                                    csv_line.append(dataset[i][el][row][0])
                                csv_data.append(csv_line)

                    # for PDF table
                    if is_vertical_ope:
                        frame_col_width = table_frame_calc_w[0]
                        index_col_width = frame_col_width * VERTICAL_INDEX_COLUMN_RATIO
                        digit_col_width = (frame_col_width - index_col_width) / vertical_digit_width
                        slot_height = row_heights[0]

                        blank_columns = []
                        filled_columns = []
                        for col_idx in range(len(dataset)):
                            data_index, vals_a, operator_mark, vals_b, equal_marks, vals_c = dataset[col_idx]
                            blank_rows = []
                            filled_rows = []
                            for row_idx in range(ini.rows):
                                block_args = (
                                    data_index[row_idx][0], vals_a[row_idx][0],
                                    operator_mark[row_idx][0], vals_b[row_idx][0]
                                )
                                blank_rows.append([get_vertical_calc_block(
                                    *block_args, '', vertical_digit_width,
                                    index_col_width, digit_col_width, slot_height,
                                    vertical_font_size, grid_color
                                )])
                                filled_rows.append([get_vertical_calc_block(
                                    *block_args, vals_c[row_idx][0], vertical_digit_width,
                                    index_col_width, digit_col_width, slot_height,
                                    vertical_font_size, grid_color
                                )])
                            blank_column_table = Table(blank_rows, colWidths=[frame_col_width], rowHeights=row_heights)
                            filled_column_table = Table(filled_rows, colWidths=[frame_col_width], rowHeights=row_heights)
                            for column_table in (blank_column_table, filled_column_table):
                                column_table.setStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')])
                            blank_columns.append(blank_column_table)
                            filled_columns.append(filled_column_table)

                        #!!! In case of next_content == None is ini.merge == False
                        #!!! or ini.merge == True but next_content == None
                        active_columns = blank_columns if next_content is None else next_content
                        for col_idx in range(len(active_columns)):
                            contents[0].append(active_columns[col_idx])
                            contents[0].append(FrameBreak())
                            if ini.merge is False:
                                contents[1].append(filled_columns[col_idx])
                                contents[1].append(FrameBreak())

                        if ini.with_bottom_answer:
                            contents[0].append(get_bottom_results(
                                dataset, tbl2_w, tbl2_h, grid_color
                            ))
                        for i in range(len(contents)):
                            contents[i].append(FrameBreak())
                        if ini.merge and next_content is None:
                            next_content = filled_columns
                        else:
                            next_content = None
                            virtual_page_counter += 1
                        continue

                    vertical_contents = get_vertical_contents(
                        dataset, row_heights, table_frame_calc_w
                        , align, valign, font_size, top_padding, left_padding
#                        , grid_color, text_color
                        , grid_color
                    )

#                    print(vertical_contents)

                    #!!! In case of next_content == None is ini.merge == False
                    #!!! or ini.merge == True but next_content == None
                    vc = vertical_contents if next_content is None else next_content
                    for col_idx in range(len(vc)):
                        for unit_idx in range(len(vc[col_idx])):
                            table = vc[col_idx][unit_idx]
                            if next_content is None:
                                if ini.reverse:
                                    if unit_idx < 3:
                                        contents[0].append(table)
                                elif ini.intermediate:
                                    if unit_idx != 5 and unit_idx != 7:
                                        contents[0].append(table)
                                else:
                                    if unit_idx is not len(vc[col_idx]) - 1:
                                        contents[0].append(table)
                            else:
                                contents[0].append(table)
                            contents[0].append(FrameBreak())

                            if ini.merge is False:
                                contents[1].append(table)
                                contents[1].append(FrameBreak())

                            if (ini.reverse and unit_idx > 2) \
                                    or unit_idx is len(vc[col_idx]) - 1:
                                table.setStyle([
                                    ('TEXTCOLOR', (0, 0), (-1, -1), 'red')
                                ])
                            if (ini.intermediate):
                                if (unit_idx == 5 or unit_idx == 7):
                                    table.setStyle([
                                        ('TEXTCOLOR', (0, 0), (-1, -1), 'red')
                                    ])

                    if ini.with_bottom_answer:
                        contents[0].append(get_bottom_results(
                            dataset, tbl2_w, tbl2_h, grid_color
                        ))
                    for i in range(len(contents)):
                        contents[i].append(FrameBreak())
                    if ini.merge and next_content == None:
                        next_content = vertical_contents
                    else:
                        next_content = None
                        virtual_page_counter += 1
        else:
#            virtual_page_counter = 1
#            next_content = None
            for page_index in range(ini.page):
                for _ in range(page_split):
                    for i in range(len(contents)):
                        contents[i].extend(headers)
                        contents[i].append(FrameBreak())

                    # Header Index
                    text = [f"# {virtual_page_counter}"]
                    if next_content is not None:
                        text.append('ans.')
                    for i in range(len(contents)):
                        add_header_index(contents[i], text,
                            header_index_frame_w, header_index_frame_h, grid_color
                        )

                    # Data elements
                    seed = [i for i in range(ini.a_min, ini.a_max)]
                    seed.extend([i for i in range(ini.a_min, ini.a_max)])
                    left_column_nums = random.sample(seed, 10)
                    seed = [i for i in range(ini.b_min, ini.b_max)]
                    seed.extend([i for i in range(ini.b_min, ini.b_max)])
                    top_row_nums = random.sample(seed, 10)

                    # Create data
                    table_data = [[None] * 11 for _ in range(11)]
                    table_data_ans = [[None] * 11 for _ in range(11)]
                    for i in range(10):
                        table_data[0][i+1] = top_row_nums[i]
                        table_data[i+1][0] = left_column_nums[i]
                        table_data_ans[0][i+1] = top_row_nums[i]
                        table_data_ans[i+1][0] = left_column_nums[i]

                    # Fill in ansers
                    for r in range(10):
                        for i in range(10):
                            table_data_ans[r+1][i+1] = \
                                table_data_ans[r+1][0] + table_data_ans[0][i+1]

                    # Add Table for 100 seq.
                    tables = []
                    table_datas = [table_data, table_data_ans]
                    for i in range(2):
                        tables.append(Table(table_datas[i]
                            , colWidths = [top_body_region_w / 11] * 11
                            , rowHeights = [top_body_region_w / 11] * 11
                        ))
                        tables[i].setStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 16),
                            ('TOPPADDING', (0, 0), (-1, -1), -7),
                        ])
                    if ini.merge is False:
                        for i in range(len(contents)):
                            contents[i].append(tables[i])
                            contents[i].append(FrameBreak())
                            contents[i].append(FrameBreak())
                        virtual_page_counter += 1
                    else:
                        if next_content == None:
                            contents[0].append(tables[0])
                            next_content = tables[1]
                        else:
                            contents[0].append(next_content)
                            next_content = None
                            virtual_page_counter += 1
                        contents[0].append(FrameBreak())
                        contents[0].append(FrameBreak())

                    # for CSV
                    if ini.csv or ini.debug:
                        for i in range(len(table_data_ans)):
                            csv_data.append(table_data_ans[i])

        # Build PDF
        if ini.merge is False:
            for i in range(len(docs)):
                docs[i].build(contents[i])
                print('export PDF')
        else:
            docs[0].build(contents[0])
            print('export PDF')

        # Write CSV
        if ini.csv or ini.debug:
            with open(OUTFILE_NAME_CSV, 'w') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            print('export CSV')

        print("All done")
    except Exception as e:
        failure(e)
#        print("Error:", e)


if __name__ == "__main__":
    args = _init()
    main(args)
