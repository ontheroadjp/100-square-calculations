#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
#import math
from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, landscape, portrait
from reportlab.platypus import BaseDocTemplate, PageTemplate
from reportlab.platypus import Frame, FrameBreak
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
        , help = 'Paper size of output PDF'
    )
    parser.add_argument('command'
        , type = str
        , choices = ['ope', 'operations', 'comp', 'complements', '100']
        , help = 'To determine what kind of print output'
    )
    parser.add_argument('-o', '--operator'
        , type = str
        , default = '+'
        , choices = ['+', '-', '*', '/']
        , nargs="*"
        , help = 'formular operator(s)'
    )
    parser.add_argument('--a-min'
        , type = int
        , default = 10
        , help = 'seed number min value of a '
    )
    parser.add_argument('--a-max'
        , type = int
        , default = 99
        , help = 'seed number max value of a '
    )
    parser.add_argument('--b-min'
        , type = int
        , default = 0
        , help = 'seed number min value of b '
    )
    parser.add_argument('--b-max'
        , type = int
        , default = 99
        , help = 'seed number max value of b '
    )
    parser.add_argument('-r', '--rows'
        , type = int
        , default = 10
        , help = 'Number of rows'
    )
    parser.add_argument('-c', '--columns'
        , type = int
        , default = 3
        , help = 'Number of columns'
    )
    parser.add_argument('--out-file'
        , default = 'result.pdf'
        , help = 'Output file path'
    )
    args = parser.parse_args()
    return args

def get_random_nums(order=10, min=1, max=9):
    """
    Generate random numbers

    Args:
        order: int
            number of list length
        min: int
            minimum number of a seed for the random number
        max: int
            maximum number of a seed for the random number

    Returns:
        args: list
            random numbers
    """
    min_max_list = list(range(min, max + 1))
    random.shuffle(min_max_list)
    random_num = []
    for i in range(order):
        random_num.append(random.choice(min_max_list))
    return random_num


def get_complement_data(nums_a, target=100, include_num=False):
    """
    Create complement from target of nums_s

    Args:
        nums_a: list
            List of seed numbers for using develop complemention
        target: int
            Complement target number
        include_number: bool, optional
            Whether to include the number before the complemention (default is False)

    Returns:
        complements: list
            List of the four operations in the format like "a + b = c" or "c = a + b"
            [0] = no answer, [1] = with answer
    """
    complements = []
    complements_w_answer = []
    count = 1
    for num in nums_a:
        c = target - num
        comp = f"{num} =>"
        comp_w_answer = f"{num} => {c}"
        if include_num:
            complements.append(str(count) + ' )  ' + comp)
            complements_w_answer.append(str(count) + ' )  ' + comp_w_answer)
        else:
            complements.append(comp)
            complements_w_answer.append(comp_w_answer)
        count += 1
    return [complements, complements_w_answer]


def get_four_operation_data(nums_a, nums_b, operators=['+', '-', '*', '/']):
    """
    Create the four operations from num_a and num_b.

    Args:
        nums_a: list
            List of seed numbers for using develop the four operations
        nums_b: list
            List of seed numbers for using develop the forur operations
        operators: list
            List of operator symbol

    Returns:
        the four operations: list
            List of the four operation elements
    """
    data_no = []
    vals_a = []
    operator_mark = []
    vals_b = []
    equal_mark = []
    vals_c = []
    print_style = {'+':'+' , '-':'-' , '*':'×' , '/':'÷'}
    counter = 1
    for _ in range(len(nums_a)):
        random.shuffle(operators)
        for operator in operators:
            a = random.choice(nums_a)
            b = random.choice(nums_b)
            if operator == '+':
                c = a + b
            elif operator == '-':
                while True:
                    # Make sure the answer is not a negative number.
                    if a - b > 0:
                        c = a - b
                        break
                    a = random.choice(nums_a)
                    b = random.choice(nums_b)
            elif operator == '*':
                c = a * b
            elif operator == '/':
                while True:
                    # Only if not divisible by zero and divisible by
                    if b != 0 and a % b == 0:
                        c = a // b
                        break
                    a = random.choice(nums_a)
                    b = random.choice(nums_b)
            counter_str = str(counter) + ')'
            data_no.append([counter_str])
            vals_a.append([str(a)])
            operator_mark.append([str(print_style[operator])])
            vals_b.append([str(b)])
            equal_mark.append(['='])
            vals_c.append([str(c)])

#            data_no.append(str(counter))
#            vals_a.append(str(a))
#            operator_mark.append(str(print_style[operator]))
#            vals_b.append(str(b))
#            equal_mark.append('=')
#            vals_c.append(str(c))
            counter += 1
    return [data_no, vals_a, operator_mark, vals_b, equal_mark, vals_c]


def create_paragraph_table(
        data_list, table_width, table_height, font_size, num_rows=15, num_columns=2):
    """
    Create a table containing data.

    Args:
        data_list: list
            List of data_list
        table_height: int
            Table height
        font_size: int
            Font size for the table in pt
        num_rows: int, optional
            Number of table rows (default is 10)
        num_columns: int, optional
            Number of table columns (default is 3)

    Returns:
        table: table object
            Table containing table data
    """
    # insert table data
#    rows = [data_list[i*num_columns:(i+1)*num_columns] for i in range(num_rows)]
    rows = data_list
#    table_data = [[Paragraph(col, ParagraphStyle(name='Operation', fontName='Helvetica', fontSize=font_size, keepWithNext=True)) for col in row] for row in rows]
    table_data = []
    for row in rows:
        paragraph_row = []
        for col in row:
            paragraph = Paragraph(col, ParagraphStyle(
                name='Operation'
                , fontName='Helvetica'
                , fontSize=font_size
                , keepWithNext=True
                , alignment=1
            ))
            paragraph_row.append(paragraph)
        table_data.append(paragraph_row)
    table = Table(
        table_data
        , rowHeights = [table_height / num_rows] * num_rows
        , colWidths = [table_width / num_columns] * num_columns
    )
    return table


#def create_100seq_table(table_width, font_size, top_row_nums, left_column_nums):
def create_100seq_table(table_width, top_row_nums, left_column_nums):
    """
    Create 100 square calculations

    Args:
        table_width: [int | float]
            table width
        top_row_nums: list
            numbers for top row as list type
        left_column_nums: list
            numbers for column as list type

    Returns:
        table: table object
            100 sequare table object for PDF
    """
    table_data = [[None] * 11 for _ in range(11)]
    for i in range(10):
        table_data[0][i+1] = top_row_nums[i]
        table_data[i+1][0] = left_column_nums[i]
    # Create table
    table = Table(
        table_data
        , colWidths = [table_width // 11] * 11
        , rowHeights = [table_width // 11] * 11
    )
    return table

#def addPageNumber(canvas, doc):
#    """
#    Add the page number
#    # https://docs.reportlab.com/reportlab/userguide/ch2_graphics/
#    """
#    page_num = canvas.getPageNumber()
#    page_no = "Page #%s" % page_num
#    canvas.setFont("Helvetica", 8)
#    width, height = doc.pagesize
#    #canvas.line(25,45,550,45)
#    canvas.drawRightString(width - 25, 25, page_no)
#    copyright = 'Copyright(c) 2024 Nuts Education'
#    canvas.drawString(25, 25, copyright)


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
    if(ini.paper_size == 'A4' or ini.paper_size == 'a4'):
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
    elif(ini.paper_size == 'B5' or ini.paper_size == 'b5'):
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
#        print(210 * mm)
#        print(297 * mm)
#        print('-------------------------')

        frames = []
        show = 0 # print Frame border # 0: hidden, 1: show

        # header frame
        header_frame_h = 50 * mm
        header_frame_w = paper_width - left_margin - right_margin
        header_frame_x = left_margin
        header_frame_y = paper_height - top_margin - header_frame_h
        frames.append(
            Frame(header_frame_x, header_frame_y
                    , header_frame_w, header_frame_h
                    , leftPadding=0, bottomPadding=0
                    , rightPadding=6, topPadding=6
                    , showBoundary = show
                  )
        )

        # body frame
        body_frame_w = paper_width - left_margin - right_margin
        body_frame_h = paper_height - top_margin - header_frame_h - bottom_margin

        # table frame
        if ini.command == 'operation' or ini.command == 'ope' \
                or ini.command == 'complements' or ini.command == 'comp':
            table_frame_w = body_frame_w // ini.columns
#            print(table_frame_w)
            table_frame_w = body_frame_w // (ini.columns * 6)
#            print(table_frame_w)
            table_frame_h = body_frame_h

            data = []
            for i in range(6):
                data.append(table_frame_w)
            w_ratio = [2.5, 3, 1.5, 2, 1.8, 5]
            calc_w = calc_table_frame_width(data, w_ratio)

            offset = 0
            for i in range((ini.columns * 6)):
                if i > 5:
                    calc_w.extend(calc_w)
#                w = table_frame_w
                w = calc_w[i]
#                x = left_margin + table_frame_w * i
                x = left_margin + offset
                y = header_frame_y - table_frame_h
                frames.append(Frame(x, y, w, table_frame_h
                                , leftPadding=0, bottomPadding=0
                                , rightPadding=0, topPadding=0
                                , showBoundary = show
                            ))
                offset += w
        else:
            table_frame_w = body_frame_w
            table_frame_h = body_frame_h
            x = header_frame_x
            y = header_frame_y - table_frame_h
            w = header_frame_w
            h = table_frame_h
            frames.append(Frame(x, y, w, h, showBoundary = show))

        page_templats = PageTemplate("frames", frames = frames)
        doc.addPageTemplates(page_templats)

        contents = []

        # Header
        header_style = ParagraphStyle(
            name='Header', leftIndent=0, fontName='Helvetica'
            , fontSize=HEADER_FONT_SIZE
        )
        header = Paragraph(f'<b>{HEADER_STR}</b>', header_style)

        # Title
        title_style = ParagraphStyle(
            name='Title', fontName='Helvetica-Bold', fontSize=TITLE_FONT_SIZE
        )
        title = Paragraph(f'<b>{TITLE_STR}</b>', title_style)

        # Sub title
        sub_title_style = ParagraphStyle(
            name='SubTitle', leftIndent=350, fontName='Helvetica'
            , fontSize=SUB_TITLE_FONT_SIZE
        )
        sub_title = Paragraph(f'<b>{SUB_TITLE_STR}</b>', sub_title_style)

        # Date and Time
        #now = datetime.now()
        date_time_style = ParagraphStyle(name='DateTime', fontSize=date_time_font_size)
        date = Paragraph(f"<b>{DATE_LABEL}</b> {'_' * 15}", date_time_style)
        time = Paragraph(f"<b>{TIME_LABEL}</b> {'_' * 15}", date_time_style)

        # Combine date and time horizontally
        date_time = Table([[date, time]], colWidths=[55 * mm, 55 * mm])
        date_time.setStyle([
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ])

        headers = [
            header, Spacer(1, 0),
            title, Spacer(1, 60),
#            sub_title, Spacer(1, 10),
            date_time
        ]

        # ------------------------------------------------
        print_type = 100
        print_type = 'ope' # operation
        print_type = 'comp' # complement
        print_type = ini.command
        # ------------------------------------------------

        # table spec
        num_rows = ini.rows
        num_columns = ini.columns
        data_size = num_rows * 1 # num_rows * num_columns
        table_frame_h = table_frame_h - 30

        page = 2
        # Create four operations table
        if print_type == 'ope' or print_type == 'operations':
            for page_index in range(page):
                contents.extend(headers)
                contents.append(FrameBreak())

                nums_a = get_random_nums(data_size, 10, 99)
                nums_b = get_random_nums(data_size, 1, 9)
                operators = ini.operator

                # create table
                for column_index in range(num_columns):
                    data = get_four_operation_data(nums_a, nums_b, operators)
                    for data_index in range(6):


#                        table = create_paragraph_table(
#                            data[data_index]
#                            , calc_w[data_index]
#                            , table_frame_h
#                            , table_font_size
#                            , num_rows
#                            , 1
#                        )
#                        table.setStyle([
#                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
#                            , ('GRID', (0, 0), (-1, -1), 0, colors.blue)
#                        ])

                        row_heights = [table_frame_h / num_rows] * num_rows
                        table = Table(data[data_index]
                                    , rowHeights = row_heights
                                    , colWidths = calc_w[data_index]
                                )
                        table_align = [
                            'RIGHT', 'RIGHT', 'CENTER', 'LEFT', 'CENTER', 'LEFT'
                        ]
                        table_valign = [
                            'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE', 'MIDDLE'
                        ]
                        fs = [ 10, 16, 16, 16, 16, 16 ]
                        tp = [ 8, 0, 0, 0, 0, 0 ]
                        lp = [ 4, 0, 0, 0, 0, 2 ]
                        rp = [ 12, 2, 2, 2, 2, 2 ]
                        table.setStyle([
                            ('ALIGN', (0, 0), (-1, -1), table_align[data_index])
                            , ('VALIGN', (0, 0), (-1, -1), table_valign[data_index])
                            , ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
                            , ('FONTSIZE', (0, 0), (-1, -1), fs[data_index])
                            , ('TOPPADDING', (0, 0), (-1, -1), tp[data_index])
                            , ('LEFTPADDING', (0, 0), (-1, -1), lp[data_index])
                            , ('GRID', (0, 0), (-1, -1), 0, colors.white)
                        ])
                        contents.append(table)
                        contents.append(FrameBreak())

        # Create 100 seq table
        elif print_type == str(100):
            contents.extend(headers)
            contents.append(FrameBreak())
            top_row_nums = get_random_nums(10, 1, 9)
            left_column_nums = get_random_nums(10, 1, 9)
            table = create_100seq_table(
                table_frame_w
#                , table_font_size
                , top_row_nums
                , left_column_nums
            )
            table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 20),
                ('TOPPADDING', (0, 0), (-1, -1), -10),
            ])
            table_w_answer = create_100seq_table(
                table_frame_w
                , top_row_nums
                , left_column_nums
            )
            contents.append(table)
            contents.append(FrameBreak())

        # Create complement table
        elif print_type == 'comp' or print_type == 'complements':
            contents.extend(headers)
            contents.append(FrameBreak())
            target = 30
            random_nums = get_random_nums(data_size, 1, target - 1)
            data = get_complement_data(random_nums, target)
            table = create_paragraph_table(
                data[0], table_frame_h, table_font_size, num_rows, num_columns
            )
            table_w_answer = create_paragraph_table(
                data[1], table_frame_h, table_font_size, num_rows, num_columns
            )
            contents.append(table)
            contents.append(FrameBreak())

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
