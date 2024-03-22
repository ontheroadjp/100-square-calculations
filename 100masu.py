#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
#import math
from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, landscape, portrait
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
        , choices = ['A4', 'B5', 'a4', 'b5']
        , help = 'Paper size of prints to be output'
    )
    parser.add_argument('command'
        , type = str
        , choices = ['99', 'ope', 'operation', 'com', 'complement', '100', 'aBc']
        , help = 'Type of formula to output'
    )
    parser.add_argument('-a', '--a-digits'
        , type = int
        , help = 'Number of digits in the first term of the formula'
    )
    parser.add_argument('-b', '--b-digits'
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
    parser.add_argument('--kuku-dan'
        , type = int
        , choices = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        , help = 'Multiplication table for'
    )
    parser.add_argument('--kuku-reverse'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in reverse order'
    )
    parser.add_argument('--kuku-shuffle'
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
        , default = 3
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

    if args.command == '99':
        args.rows = 9

    digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
    if args.a_digits is not None:
        args.a_min, args.a_max = digits_list[args.a_digits - 1]
    else:
        args.a_min, args.a_max = (args.a_min, args.a_max)
    if args.b_digits is not None:
        args.b_min, args.b_max = digits_list[args.b_digits - 1]
    else:
        args.b_min, args.b_max = (args.b_min, args.b_max)
    return args


def add_vertical_frame_set(frames, start_x, start_y, region_w, region_h, frame_amount, w_ratio, show):
    table_frame_w = region_w / frame_amount
    table_frame_h = region_h

    table_frame_w_list = []
    [table_frame_w_list.append(table_frame_w) for i in range(len(w_ratio))]
    #w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]

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


def get_kuku_data(dan, columns = 2, print_index = 1, is_reverse = False, is_shuffle = False):
    """
    Create the 99 operations

    Args:
        dan: int
            Create the 99 for
        order: int
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
    val_b = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if is_reverse:
        val_b.reverse()
    if is_shuffle:
        random.shuffle(val_b)
    for i in range(len(val_b)):
        c = dan * val_b[i]
        counter_str = str(print_index) + ')'
        data_index.append([counter_str])
        vals_a.append([dan])
        operator_marks.append(['×'])
        vals_b.append([str(val_b[i])])
        equal_marks.append(['='])
        vals_c.append([str(c)])
        print_index += 1
    return (data_index, vals_a, operator_marks, vals_b, equal_marks, vals_c)


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


def add_vertical_content(table_type, contents, data_elements
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
        if table_type == '99':
            dan, cols, is_reverse, is_shuffle = data_elements
            data = get_kuku_data(dan, cols, print_index, is_reverse, is_shuffle)
        elif table_type == 'operation' or table_type == 'ope':
            nums_a, nums_b, operator = data_elements
            data = get_operation_data(
                nums_a, nums_b, operator, data_order, print_index)
        elif table_type == 'complement' or table_type == 'com':
            target, random_nums = data_elements
            data = get_complement_data(
                random_nums, target, data_order, print_index)
        elif table_type == 'aBc':
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
            table = Table(data[data_index]
                , rowHeights = row_heights
                , colWidths = col_widths[data_index]
            )
            table.setStyle([
                ('ALIGN', (0, 0), (-1, -1), align[data_index])
                , ('VALIGN', (0, 0), (-1, -1), valign[data_index])
                , ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
                , ('FONTSIZE', (0, 0), (-1, -1), font_size[data_index])
                , ('TEXTCOLOR', (0, 0), (-1, -1), text_color[data_index])
                , ('TOPPADDING', (0, 0), (-1, -1), top_padding[data_index])
                , ('LEFTPADDING', (0, 0), (-1, -1), left_padding[data_index])
                , ('GRID', (0, 0), (-1, -1), 0, grid_color)
            ])
            contents.append(table)
            contents.append(FrameBreak())
    if len(result_vals_for_print):
        calc_results.append(result_vals_for_print)
    if with_bottom_answer:
        row_heights = [tbl2_h / len(calc_results)] * len(calc_results)
        col_widths = [tbl2_w / 20] * 20
        table = Table(calc_results
            , rowHeights = row_heights
            , colWidths = col_widths
        )
        table.setStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9)
            , ('ALIGN', (0, 0), (-1, -1), 'CENTER')
            , ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')
            , ('GRID', (0, 0), (-1, -1), 0, grid_color)
        ])
        contents.append(table)
    contents.append(FrameBreak())


def addPageNumber(canvas, doc):
    """
    Add the page number
    # https://docs.reportlab.com/reportlab/userguide/ch2_graphics/
    """
    page_num = canvas.getPageNumber()
    page_no = "Page #%s" % page_num
    canvas.setFont("Helvetica", 8)
    width, height = doc.pagesize
    #canvas.line(25,45,550,45)
    canvas.drawRightString(width - 25, 25, page_no)
    copyright = 'Copyright(c) 2024 Nuts Education'
    canvas.drawString(25, 25, copyright)


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
#    FONT = "Helvetica"
#    FONT = "Courier"
    if ini.paper_size.lower() == 'a4':
        paper_width, paper_height = A4
        top_margin = 20 * mm
        bottom_margin = 20 * mm
        left_margin = 20 * mm
        right_margin = 20 * mm

        header_font_size = 14
        title_font_size = 24
        sub_title_font_size = 10
        date_time_font_size = 10
        table_font_size = 12
    elif ini.paper_size.lower() == 'b5':
        paper_width, paper_height = B5
        top_margin = 20 * mm
        bottom_margin = 20 * mm
        left_margin = 20 * mm
        right_margin = 20 * mm

        header_font_size = 12
        title_font_size = 18
        sub_title_font_size = 8
        date_time_font_size = 8
        table_font_size = 10
    try:
        # Create PDF
        OUT_FILENAME = ini.out_file
        doc = BaseDocTemplate(
            OUT_FILENAME
            , topMargin = top_margin
            , leftMargin = left_margin
            , rightMargin = right_margin
            , bottomMargin = bottom_margin
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
#        print(210 * mm) # A4
#        print(297 * mm) # A4
#        print(182 * mm) # B5
#        print(257 * mm) # B5
#        print('-------------------------')

        frames = []
        show = 0
        if ini.debug:
            show = 1 # print Frame border # 0: hidden, 1: show

        # header frame
        header_region = (paper_width - left_margin - right_margin, 40 * mm)
        header_region_x = left_margin
        header_region_y = paper_height - top_margin - header_region[1]

        x = header_region_x
        y = header_region_y
        w = header_region[0]
        h = header_region[1]
        frames.append(Frame(x, y, w, h
            , leftPadding = 0, bottomPadding = 0
            , rightPadding = 0, topPadding = 0
            , showBoundary = show
        ))

        # body region
        body_region = (
            paper_width - left_margin - right_margin
            , paper_height - top_margin - header_region[1] - bottom_margin
        )

        # bottom body region
        bottom_body_region = (body_region[0], 25 * mm)

        # top body region
        top_body_region = (body_region[0], body_region[1] - bottom_body_region[1])

        table_frame_calc_w = []
        if ini.command == 'operation' or ini.command == 'ope' \
                or ini.command == '99':
            x = left_margin
            y = header_region_y - body_region[1] + bottom_body_region[1]
            w = top_body_region[0]
            h = top_body_region[1]
            frame_amount = ini.columns * 6
            if ini.paper_size.lower() == 'a4':
                w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
            elif ini.paper_size.lower() == 'b5':
                w_ratio = [4.0, 3.2, 1.2, 2.5, 1.2, 3.2]
            table_frame_calc_w = add_vertical_frame_set(
                frames, x, y, w, h, frame_amount, w_ratio, show
            )
        elif ini.command == '100':
            x = header_region_x
            y = header_region_y - top_body_region[1]
            w = header_region[0]
            h = body_region[0]
            frames.append(Frame(x, y, w, h
                , leftPadding = 0, bottomPadding = 0
                , rightPadding = 0, topPadding = 0
                , showBoundary = show
            ))
        elif ini.command == 'complement' or ini.command == 'com' \
                or ini.command == 'aBc':
            x = left_margin
            y = header_region_y - body_region[1] + bottom_body_region[1]
            w = top_body_region[0]
            h = top_body_region[1]
            frame_amount = ini.columns * 4
            if ini.paper_size.lower() == 'a4':
                w_ratio = [1, 1, 1, 1]
            elif ini.paper_size.lower() == 'b5':
                w_ratio = [1, 1, 1, 1]
            table_frame_calc_w = add_vertical_frame_set(
                frames, x, y, w, h, frame_amount, w_ratio, show
            )

        # Table 2 frame
        tbl2_w = body_region[0]
        tbl2_h = bottom_body_region[1]
        tbl2_x = left_margin
        tbl2_y = header_region_y - top_body_region[1] - tbl2_h
        frames.append(Frame(tbl2_x, tbl2_y, tbl2_w, tbl2_h
            , leftPadding=0, bottomPadding=0
            , rightPadding=0, topPadding=0
            , showBoundary = show
        ))

#        page_templats = PageTemplate("frames", frames = frames)
#        page_templats = PageTemplate("frames", frames=frames
#                            , onPage=addPageNumber, onPageEnd=addPageNumber)
        page_templats = PageTemplate("frames", frames=frames, onPage=addPageNumber)
        doc.addPageTemplates(page_templats)

        contents = []

        # Header
        header_style = ParagraphStyle(
            name='Header', leftIndent=0, fontName='Helvetica'
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
            colWidths = [header_region[0] / 2] * 2
        )
        date_time.setStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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
        row_heights = [(top_body_region[1] - 40) / rows] * rows
        if table_frame_calc_w:
            col_widths = table_frame_calc_w

        # Generic Table Style (for 6 columns / unit)
        align = ('RIGHT', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'LEFT')
        valign = ('MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE')
        if ini.paper_size.lower() == 'a4':
            font_size = (10, 16, 16, 16, 16, 16)
        if ini.paper_size.lower() == 'b5':
            font_size = (8, 12, 12, 12, 12, 12)
        top_padding = (4, 0, -2, 0, 0, -2)
        left_padding = (4, 4, 4, 4, 4, 4)
        grid_color = colors.white
        text_color = ( 'black', 'black', 'black', 'black', 'black', 'white' )
        if ini.with_answer or ini.debug:
            text_color = ( 'black', 'black', 'black', 'black', 'black', 'black' )
        if ini.debug:
            grid_color = colors.blue

        # Create four 99 table
        if ini.command == 'kuku' or ini.command == '99':
            for page_index in range(ini.page):
                contents.extend(headers)
                contents.append(FrameBreak())

                # Data elements
                data_elements = (
                    ini.kuku_dan, ini.columns, ini.kuku_reverse, ini.kuku_shuffle)

                # Add table
                add_vertical_content(ini.command, contents, data_elements
                    , rows, cols, row_heights, col_widths
                    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
                    , tbl2_w, tbl2_h
                    , ini.with_answer, ini.with_bottom_answer, ini.debug
                )

        if ini.command == 'operation' or ini.command == 'ope':
            for page_index in range(ini.page):
                contents.extend(headers)
                contents.append(FrameBreak())

                # Data elements
                seed = [i for i in range(ini.a_min, ini.a_max)]
                nums_a = random.sample(seed, len(seed))
                seed = [i for i in range(ini.b_min, ini.b_max)]
                nums_b = random.sample(seed, len(seed))
                operator = ini.operator
                data_elements = (nums_a, nums_b, operator)

                # Add table
                add_vertical_content(ini.command, contents, data_elements
                    , rows, cols, row_heights, col_widths
                    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
                    , tbl2_w, tbl2_h
                    , ini.with_answer, ini.with_bottom_answer, ini.debug
                )

        # Create 100 seq table
        elif ini.command == str(100):
            for page_index in range(ini.page):
                contents.extend(headers)
                contents.append(FrameBreak())

                # Data elements
                seed = [i for i in range(1, 9)]
                seed.extend([i for i in range(1, 9)])
                top_row_nums = random.sample(seed, 10)
                left_column_nums = random.sample(seed, 10)

                # Create data
                table_data = [[None] * 11 for _ in range(11)]
                for i in range(10):
                    table_data[0][i+1] = top_row_nums[i]
                    table_data[i+1][0] = left_column_nums[i]

                # Add table
                table = Table(
                    table_data
                    , colWidths = [top_body_region[0] / 11] * 11
                    , rowHeights = [top_body_region[0] / 11] * 11
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
                contents.append(table)
#                contents.append(FrameBreak())
                contents.append(PageBreak())

        # Create complement table
        elif ini.command == 'complement' or ini.command == 'com':
            for page_index in range(ini.page):
                contents.extend(headers)
                contents.append(FrameBreak())

                # Data elements
                target = 100
                seed = [i for i in range(1, target - 1)]
                random_nums = random.sample(seed, len(seed))
                data_elements = (target, random_nums)

                # Add table
                add_vertical_content(ini.command, contents, data_elements
                    , rows, cols, row_heights, col_widths
                    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
                    , tbl2_w, tbl2_h
                    , ini.with_answer, ini.with_bottom_answer, ini.debug
                )

        # Create aBc table
        elif ini.command == 'aBc':
            for page_index in range(ini.page):
                contents.extend(headers)
                contents.append(FrameBreak())

                # Data elements
                data_elements = ()

                # Add table
                add_vertical_content(ini.command, contents, data_elements
                    , rows, cols, row_heights, col_widths
                    , align, valign, font_size, top_padding, left_padding, grid_color, text_color
                    , tbl2_w, tbl2_h
                    , ini.with_answer, ini.with_bottom_answer, ini.debug
                )

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
