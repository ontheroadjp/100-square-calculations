#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
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
        , default = 1
        , help = 'Number of digits in the first term of the formula'
    )
    parser.add_argument('-b', '--b-value'
        , type = int
        , default = 1
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
    parser.add_argument('-w', '--with-answer'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether the answer to a formula should be displayed or not'
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

    if args.command == '100' and args.a_value > 3:
        print(f"bad argument: -a {args.a_value}")
        print('It must be less than 3.')
        exit()

    if args.command == 'ope' or args.command == '100':
        digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
        if args.a_value is not None:
            args.a_min, args.a_max = digits_list[args.a_value - 1]
        if args.b_value is not None:
            args.b_min, args.b_max = digits_list[args.b_value - 1]
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


def add_vertical_content(command, contents, data_elements
    , rows, cols, row_heights, col_widths
    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
    , tbl2_w, tbl2_h
    , with_answer, with_bottom_answer, debug):

    # create table
    calc_results = []
    cumulative_index = 1
    result_vals_for_print = []
    data_order = rows * 1 # ini.rows * ini.columns
    for column_index in range(cols):
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
            contents.append(top_table)
            contents.append(FrameBreak())
    if len(result_vals_for_print):
        calc_results.append(result_vals_for_print)
    if with_bottom_answer:
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
        contents.append(bottom_table)
    contents.append(FrameBreak())


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
    margin_left = 20 * mm
    margin_right = 20 * mm

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
        OUT_FILENAME = ini.out_file
        doc = BaseDocTemplate(
            OUT_FILENAME
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

#        print(paper_width)
#        print(paper_height)
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

        frames = []

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
            frames.append(Frame(x, y, w, h
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
            frames.append(Frame(x, y, w, h
                , leftPadding = 0, bottomPadding = 0
                , rightPadding = 0, topPadding = 0
                , showBoundary = ini.debug
            ))

            # Body Region
            body_region_w = header_region_w
            body_region_h = vp_h - margin_top - header_region_h - margin_bottom

            # Bottom Body Region
            bottom_body_region_w = body_region_w
            bottom_body_region_h = 25 * mm

            # Top Body Region
            top_body_region_w = body_region_w
            top_body_region_h = body_region_h - bottom_body_region_h

            table_frame_calc_w = []
            if ini.command == 'operation' or ini.command == 'ope' \
                    or ini.command == '99' or ini.command == 'squ' \
                    or ini.command == 'pi':
                x = header_region_x
                y = header_region_y - top_body_region_h
                w = top_body_region_w
                h = top_body_region_h
                frame_amount = ini.columns * 6
                w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
#                if ini.paper_size.lower() == 'a3':
#                    w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
#                elif ini.paper_size.lower() == 'a4':
#                    w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
#                elif ini.paper_size.lower() == 'b5' or ini.paper_size.lower() == 'a4l':
#                    w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
                table_frame_calc_w = add_vertical_frame_set(
                    frames, x, y, w, h, frame_amount, w_ratio, ini.debug
                )
            elif ini.command == '100':
                x = header_region_x
                y = header_region_y - top_body_region_h
                w = header_region_w
                h = body_region_w
                frames.append(Frame(x, y, w, h
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
                frame_amount = ini.columns * 4
                w_ratio = [1, 1.5, 0.6, 1.5]
#                if ini.paper_size.lower() == 'a3':
#                    w_ratio = [1, 1, 1, 1]
#                if ini.paper_size.lower() == 'a4' or ini.paper_size.lower() == 'a4l':
#                    w_ratio = [1, 1, 1, 1]
#                elif ini.paper_size.lower() == 'b5':
#                    w_ratio = [1, 1, 1, 1]
                table_frame_calc_w = add_vertical_frame_set(
                    frames, x, y, w, h, frame_amount, w_ratio, ini.debug
                )

            # Table 2 frame
            tbl2_w = body_region_w
            tbl2_h = bottom_body_region_h
            tbl2_x = header_region_x
            tbl2_y = header_region_y - body_region_h
            frames.append(Frame(tbl2_x, tbl2_y, tbl2_w, tbl2_h
                , leftPadding=0, bottomPadding=0
                , rightPadding=0, topPadding=0
                , showBoundary = ini.debug
            ))

#        page_templats = PageTemplate("frames", frames = frames)
#        page_templats = PageTemplate("frames", frames=frames
#                            , onPage=addPageNumber, onPageEnd=addPageNumber)
        page_templats = PageTemplate("frames", frames=frames, onPageEnd=addPageNumber)
        doc.addPageTemplates(page_templats)

        contents = []

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
        cols = ini.columns
        row_heights = [(top_body_region_h - 40) / rows] * rows
        if table_frame_calc_w:
            col_widths = table_frame_calc_w

        # Generic Table Style (for 6 columns / unit)
        align = ['RIGHT', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'LEFT']
        valign = ['MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE']
        text_color = ['black', 'black', 'black', 'black', 'black', 'white']
        if ini.paper_size.lower() == 'a4':
            font_size = (10, 16, 16, 16, 16, 16)
        if ini.paper_size.lower() == 'b5' or ini.paper_size.lower() == 'a4l' \
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

        # with answer & for debug
        if ini.with_answer or ini.debug:
            text_color[-1] = 'black'
            text_color[3] = 'black'
#        if ini.debug:
#            grid_color = colors.blue

        # Document Development
        if not ini.command == '100':
            virtual_page_counter = 1
            for page_index in range(ini.page):
                for _ in range(page_split):
                    contents.extend(headers)
                    contents.append(FrameBreak())

                    # Header Index
                    add_header_index(contents, [f"# {virtual_page_counter}"],
                        header_index_frame_w, header_index_frame_h, grid_color
                    )

                    # Main Table
                    # Create Data Elements
                    data_elements = ()
                    if ini.command == '99' or ini.command == 'squ' \
                            or ini.command == 'pi':
                        data_elements = (
                                ini.command, ini.a_value, ini.reverse, ini.shuffle)
                    elif ini.command == 'operation' or ini.command == 'ope':
                        seed = [i for i in range(ini.a_min, ini.a_max)]
                        nums_a = random.sample(seed, len(seed))
                        seed = [i for i in range(ini.b_min, ini.b_max)]
                        nums_b = random.sample(seed, len(seed))
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

                    add_vertical_content(ini.command, contents, data_elements
                        , rows, cols, row_heights, col_widths
                        , align, valign, font_size, top_padding
                        , left_padding, grid_color, text_color
                        , tbl2_w, tbl2_h
                        , ini.with_answer, ini.with_bottom_answer, ini.debug
                    )
                    virtual_page_counter += 1
        else:
            virtual_page_counter = 1
            is_anser_page = False
            for page_index in range(ini.page):
                for _ in range(page_split):
                    contents.extend(headers)
                    contents.append(FrameBreak())

                    # Header Index
                    text = [f"# {virtual_page_counter}"]
                    if is_anser_page:
                        text.append('ans.')
                    add_header_index(contents, text,
                        header_index_frame_w, header_index_frame_h, grid_color
                    )

                    if not is_anser_page:
                        # Data elements
                        seed = [i for i in range(ini.a_min, ini.a_max)]
                        seed.extend([i for i in range(ini.a_min, ini.a_max)])
                        left_column_nums = random.sample(seed, 10)
                        seed = [i for i in range(ini.b_min, ini.b_max)]
                        seed.extend([i for i in range(ini.b_min, ini.b_max)])
                        top_row_nums = random.sample(seed, 10)

                        # Create data
                        table_data = [[None] * 11 for _ in range(11)]
                        for i in range(10):
                            table_data[0][i+1] = top_row_nums[i]
                            table_data[i+1][0] = left_column_nums[i]

                        # Fill in ansers
                        for r in range(10):
                            for i in range(10):
                                table_data[r+1][i+1] = \
                                    table_data[r+1][0] + table_data[0][i+1]

                    # Add Table for 100 seq.
                    table = Table( table_data
                        , colWidths = [top_body_region_w / 11] * 11
                        , rowHeights = [top_body_region_w / 11] * 11
                    )
                    table.setStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 16),
                        ('TOPPADDING', (0, 0), (-1, -1), -7),
                    ])
                    if not is_anser_page:
                        table.setStyle([('TEXTCOLOR', (1, 1), (-1, -1), 'white')])

                    contents.append(table)
                    contents.append(FrameBreak())
                    contents.append(FrameBreak())
                    if is_anser_page:
                        is_anser_page = False
                        virtual_page_counter += 1
                    else:
                        is_anser_page = True

        # Build PDF
#        doc.build(contents, onFirstPage = addPageNumber, onLaterPages = addPageNumber)
#        doc.multiBuild(contents)
        doc.build(contents)

        print("All done")
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    args = _init()
    main(args)
