#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import random
import csv
#import copy
#import math
#from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, A3, landscape, portrait
from reportlab.platypus import BaseDocTemplate, PageTemplate
from reportlab.platypus import Frame, FrameBreak, PageBreak
from reportlab.platypus import Table, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors


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
        , default = 'A4'
        , choices = ['A3', 'A4', 'B5', 'a3', 'a4', 'b5', 'a4l']
        , help = 'Paper size of prints to be output'
    )
    parser.add_argument('command'
        , type = str
        , choices = ['99', 'ope', 'operation', 'com', 'complement', '100', 'aBc', 'squ', 'pi']
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
#    parser.add_argument('-w', '--with-answer'
#        , default = False
#        , action = 'store_true'
#        , help = 'Flag whether the answer to a formula should be displayed or not'
#    )
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

    if args.command == 'ope':
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

    return args


def add_vertical_frame_set(frames, start_x, start_y, region_w, region_h, frame_amount, w_ratio, show):
    table_frame_w = region_w / frame_amount
    table_frame_h = region_h

    table_frame_w_list = []
    [table_frame_w_list.append(table_frame_w) for i in range(len(w_ratio))]

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


def get_operation_data(nums_a, nums_b, operators=['add'], order=10, print_index = 1):
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
    print_style = {'add':'+', 'sub':'-', 'mul':'×', 'div':'÷'}
    if operators.count('mix') > 0:
        operators = ['add', 'sub', 'mul', 'div']
    for _ in range(order):
        a = random.choice(nums_a)
        b = random.choice(nums_b)
        random.shuffle(operators)
        operator = random.choice(operators)
        if operator == 'add':
            c = a + b
        elif operator == 'sub':
            while True:
                # Make sure the answer is not a negative number.
                if a - b > 0:
                    c = a - b
                    break
                a = random.choice(nums_a)
                b = random.choice(nums_b)
        elif operator == 'mul':
            c = a * b
        elif operator == 'div':
            while True:
                # Only if not divisible by zero and divisible by
                if b != 0 and a % b == 0:
                    c = a // b
                    break
                a = random.choice(nums_a)
                b = random.choice(nums_b)

        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        vals_a.append([str(a)])
        operator_mark.append([str(print_style[operator])])
        vals_b.append([str(b)])
        equal_marks.append(['='])
        vals_c.append([str(c)])

        print_index += 1
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


def get_fixed_format_data(mode, start_num=1, order=10, print_index=1, is_reverse=False, is_shuffle=False):
    """
    Create the square numbers operations

    Args:
        num_min: int
            Create the 99 for
        num_max: int
            Number of creating 99 questions
        print_index: int
            begining number of question
        is_reverse: boolean
            Output in reverse order of 99
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

    if is_reverse:
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
    return (data_index, vals_a, operator_marks, vals_b, equal_marks, vals_c)


def get_aBc_data(order = 10, print_index = 1):
    nums = [a for a in range(0, 10)]

    vals_a = []
    equal_marks = []
    vals_c = []
    data_index = []
    for i in range(order):
        a = random.choice(nums)
        b = random.choice(nums)
        c = random.choice(nums)
        d = random.choice(nums)

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


def get_vertical_contents(command, data_elements
    , rows, columns, row_heights, col_widths
    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
    , tbl2_w, tbl2_h):

    # create table
    calc_results = []
    cumulative_index = 1
    result_vals_for_print = []
    data_order = rows * 1 # ini.rows * ini.columns
    vertical_contents = []
    for column_index in range(columns):
        print_index = 1 + (rows * column_index)
        if command == '99' or command == 'squ' or command == 'pi':
            mode, start_num, is_reverse, is_shuffle = data_elements
            data = get_fixed_format_data(mode, start_num, data_order, print_index, is_reverse, is_shuffle)
        elif command == 'operation' or command == 'ope':
            nums_a, nums_b, operator = data_elements
            data = get_operation_data(
                nums_a, nums_b, operator, data_order, print_index)
        elif command == 'complement' or command == 'com':
            target, random_nums = data_elements
            data = get_complement_data(
                random_nums, target, data_order, print_index)
        elif command == 'aBc':
            data = get_aBc_data(data_order, print_index)

        table_set = []
        for data_index in range(len(data)):
            if data_index == (len(data) - 1):
                for val in data[data_index]:
                    result_vals_for_print.append(f"({cumulative_index})")
                    result_vals_for_print.append(val[0])
                    cumulative_index += 1
                    if len(result_vals_for_print) > 18:
                        calc_results.append(result_vals_for_print)
                        result_vals_for_print = []
            top_table = Table(data[data_index]
                , rowHeights = row_heights
                , colWidths = col_widths[data_index]
            )
            top_table.setStyle([
                ('ALIGN', (0, 0), (-1, -1), align[data_index])
                , ('VALIGN', (0, 0), (-1, -1), valign[data_index])
                , ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
                , ('FONTSIZE', (0, 0), (-1, -1), font_size[data_index])
                , ('TEXTCOLOR', (0, 0), (-1, -1), text_color[data_index])
                , ('TOPPADDING', (0, 0), (-1, -1), top_padding[data_index])
                , ('LEFTPADDING', (0, 0), (-1, -1), left_padding[data_index])
                , ('GRID', (0, 0), (-1, -1), 0, grid_color)
            ])
            table_set.append(top_table)
        vertical_contents.append(table_set)

#    bottom_table = None
#    if with_bottom_answer:
    if len(result_vals_for_print):
        calc_results.append(result_vals_for_print)
    row_heights = [tbl2_h / len(calc_results)] * len(calc_results)
    col_widths = [tbl2_w / 20] * 20
    bottom_table = Table(calc_results
        , rowHeights = row_heights
        , colWidths = col_widths
    )
    bottom_table.setStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8)
        , ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        , ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        , ('GRID', (0, 0), (-1, -1), 0, grid_color)
    ])
    return [vertical_contents, bottom_table]


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
    try:
        # Create Document (PDF)
        OUTFILE_NAME = ini.out_file
        OUTFILE_NAME_READ = ini.out_file.rstrip('.pdf') + '_read.pdf'

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
                (0, paper_height / 2), (paper_width / 2, paper_height / 2)
                , (0, 0), (paper_width / 2, 0)
            )

        # 0: normal, 1: read
        frames = [[],[]]
#        frames = [[]] * len(docs)

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
            top_body_region_x = header_region_x
            top_body_region_y = header_region_y - top_body_region_h

            table_frame_calc_w = []
            if ini.command == 'operation' or ini.command == 'ope' \
                    or ini.command == '99' or ini.command == 'squ' \
                    or ini.command == 'pi':
                x = top_body_region_x
                y = top_body_region_y
                w = top_body_region_w
                h = top_body_region_h
                w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
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
            elif ini.command == 'complement' or ini.command == 'com' \
                    or ini.command == 'aBc':
                x = header_region_x
                y = header_region_y - top_body_region_h
                w = top_body_region_w
                h = top_body_region_h
                w_ratio = [1, 1.5, 0.6, 1.5]
                frame_amount = ini.columns * len(w_ratio)
                for i in range(len(frames)):
                    table_frame_calc_w = add_vertical_frame_set(
                        frames[i], x, y, w, h, frame_amount, w_ratio, ini.debug
                    )

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
        header_style = ParagraphStyle(
            name='Header', leftIndent=0, fontName='Courier-Bold'
            , fontSize=header_font_size
        )
        header = Paragraph(f'<b>{HEADER_STR}</b>', header_style)

        # Title
        title_style = ParagraphStyle(
            name='Title', fontName='Helvetica-Bold', fontSize=title_font_size
        )
        title = Paragraph(f'<b>{TITLE_STR}</b>', title_style)

        # Sub title
        sub_title_style = ParagraphStyle(
            name='SubTitle', leftIndent=350, fontName='Helvetica'
            , fontSize=sub_title_font_size
        )
        sub_title = Paragraph(f'<b>{SUB_TITLE_STR}</b>', sub_title_style)

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
        rows = ini.rows
        columns = ini.columns
        row_heights = [(top_body_region_h - 0) / rows] * rows
        if ini.with_bottom_answer:
            row_heights = [(top_body_region_h - 20) / rows] * rows
        if table_frame_calc_w:
            col_widths = table_frame_calc_w

        # Generic Table Style (for 6 columns / unit)
        align = ['RIGHT', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'LEFT']
        valign = ['MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE']
        text_color = ['black', 'black', 'black', 'black', 'black', 'black']
        if ini.paper_size.lower() == 'a4':
            font_size = (10, 16, 16, 16, 16, 16)
        if ini.paper_size.lower() == 'b5' \
                or ini.paper_size.lower() == 'a4l' \
                or ini.paper_size.lower() == 'a3':
            font_size = (7, 11, 11, 11, 11, 11)
        grid_color = colors.white if not ini.debug else colors.blue
        top_padding = (5, 0, -2, 0, -2, 0)
        left_padding = (4, 4, 2, 4, 4, 4)

        # Generic Table Style (for 4 columns / unit)
        if ini.command == 'com' or ini.command == 'aBc':
            align[3] = 'LEFT'
            text_color[3] = 'white'
            font_size = (7, 11, 9, 11)

        # for debug
        if ini.debug:
            text_color[-1] = 'black'
            text_color[3] = 'black'
        # Document Development
        if not ini.command == '100':
            virtual_page_counter = 1
#            data_csv_lines = []
            for page_index in range(ini.page):
                next_content = None
                for _ in range(page_split):
                    # Header & Header Index
                    for i in range(len(contents)):
                        contents[i].extend(headers)
                        contents[i].append(FrameBreak())
                        add_header_index(contents[i], [f"# {virtual_page_counter}"],
                            header_index_frame_w, header_index_frame_h, grid_color
                        )

                    # Main Table
                    # Create Data Elements
                    data_elements = ()
                    if ini.command == '99' or ini.command == 'squ' \
                            or ini.command == 'pi':
                        data_elements = (
                            ini.command, ini.a_value, ini.reverse, ini.shuffle
                        )
                    elif ini.command == 'operation' or ini.command == 'ope':
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
                        operator = ini.operator
                        data_elements = (nums_a, nums_b, operator)
                    elif ini.command == 'complement' or ini.command == 'com':
                        # Data elements
                        target = ini.a_value
                        seed = [i for i in range(1, target - 1)]
                        random_nums = random.sample(seed, len(seed))
                        data_elements = (target, random_nums)
                    elif ini.command == 'aBc':
                        data_elements = ()

                    vertical_contents = get_vertical_contents(
                        ini.command, data_elements
                        , rows, columns, row_heights, col_widths
                        , align, valign, font_size, top_padding, left_padding
                        , grid_color, text_color
                        , tbl2_w, tbl2_h
                    )

                    # In case of next_content == None is ini.merge == False
                    # or ini.merge == True but next_content == None
                    vc = vertical_contents if next_content is None else next_content

                    for col_idx in range(len(vc[0])):
                        for unit_idx in range(len(vc[0][col_idx])):
                            table = vc[0][col_idx][unit_idx]
                            if next_content is None:
                                if unit_idx is not len(vc[0][col_idx]) - 1:
                                    contents[0].append(table)
                            else:
                                contents[0].append(table)
                            contents[0].append(FrameBreak())

                            if ini.merge is False:
                                contents[1].append(table)
                                contents[1].append(FrameBreak())

                            if unit_idx is len(vc[0][col_idx]) - 1:
                                table.setStyle([
                                    ('TEXTCOLOR', (0, 0), (-1, -1), 'red')
                                ])

                    if ini.with_bottom_answer:
                        contents[0].append(vertical_contents[1])
                    for i in range(len(contents)):
                        contents[i].append(FrameBreak())

                    if ini.merge and next_content == None:
                        next_content = vertical_contents
                    else:
                        next_content = None
                        virtual_page_counter += 1

#                    # CSV
#                    for column_idx in range(len(dataset)):
#                        for row_idx in range(len(dataset[column_idx][0])):
#                            csv_line = [page_index]
#                            for element_idx in range(len(dataset[column_idx])):
#                                csv_line.append(
#                                    dataset[column_idx][element_idx][row_idx][0].rstrip(')')
#                                )
#                            data_csv_lines.append(csv_line)
#            # Write CSV
#            csv_file_name = ini.out_file.rstrip('.pdf') + '.csv'
#            with open(csv_file_name, 'w') as f:
#                writer = csv.writer(f)
#                writer.writerows(data_csv_lines)

        else:
            virtual_page_counter = 1
            for page_index in range(ini.page):
                next_content = None
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

#            # Write CSV
#            csv_file_name = ini.out_file.rstrip('.pdf') + '.csv'
#            with open(csv_file_name, 'w') as f:
#                writer = csv.writer(f)
#                writer.writerows(table_data)

        # Build PDF
        if ini.merge is False:
            for i in range(len(docs)):
                docs[i].build(contents[i])
                print('export PDF')
        else:
            docs[0].build(contents[0])
            print('export PDF')

        print("All done")
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    args = _init()
    main(args)
