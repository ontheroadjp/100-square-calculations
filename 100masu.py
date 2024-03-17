#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, landscape, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm

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
    parser.add_argument('-s', '--serial-number'
        , action='store_true'
        , default = False
        , help = 'Show serial number'
    )
    parser.add_argument('--reverse'
        , action='store_true'
        , default = False
        , help = 'Show reverse formula'
    )
    parser.add_argument('--out-file'
        , default = 'result.pdf'
        , help = 'Output file path'
    )
    args = parser.parse_args()
    return args

def get_random_nums(num=10, min=1, max=9):
    """
    Generate random numbers

    Args:
        num: int
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
    for i in range(num):
        random_num.append(random.choice(min_max_list))
    return random_num


def get_complement_list(nums_a, target=100, include_num=False):
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


def get_four_operation_data(nums_a, nums_b, operators=['+', '-', '*', '/']
                , include_num=False, is_reverse=False):
    """
    Create the four operations from num_a and num_b.

    Args:
        nums_a: list
            List of seed numbers for using develop the four operations
        nums_b: list
            List of seed numbers for using develop the forur operations
        include_number: bool, optional
            Whether to include the number before the four operations (default is False)
        include_answer: bool, optional
            Whether to include the answer in the four operations (default is True)
        is_reverse: bool, optional
            Output the four operations reversed (default is False)

    Returns:
        the four operations: list
            List of the four operations in the format like "a + b = c" or "c = a + b"
            [0] = no answer, [1] = with answer
    """
    four_operations = []
    four_operations_w_answer = []
    print_style = {'+':'+' , '-':'-' , '*':'×' , '/':'÷'}
    count = 1
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
            if is_reverse:
                ope = f"{c} = "
                ope_w_answer = f"{c} = {a} {print_style[operator]} {b}"
            else:
                ope = f"{a} {print_style[operator]} {b} = "
                ope_w_answer = f"{a} {print_style[operator]} {b} = {c}"
            if include_num:
                four_operations.append(str(count) + ' )  ' + ope)
                four_operations_w_answer.append(str(count) + ' )  ' + ope_w_answer)
            else:
                four_operations.append(ope)
                four_operations_w_answer.append(ope_w_answer)
            count += 1
    return [four_operations, four_operations_w_answer]


def create_basic_table(
        data_list, table_height, font_size, num_rows=15, num_columns=2):
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
    rows = [data_list[i*num_columns:(i+1)*num_columns] for i in range(num_rows)]
#    table_data = [[Paragraph(cell, ParagraphStyle(name='Operation', fontName='Helvetica', fontSize=font_size, keepWithNext=True)) for cell in row] for row in rows]
    table_data = []
    for row in rows:
        # 行の各セルを段落オブジェクトに変換し、リストに追加
        paragraph_row = []
        for cell in row:
            paragraph = Paragraph(cell, ParagraphStyle(
                                            name='Operation'
                                            , fontName='Helvetica'
                                            , fontSize=font_size
                                            , keepWithNext=True)
                                        )
            paragraph_row.append(paragraph)
        table_data.append(paragraph_row)
    table = Table(
        table_data
        #, colWidths = [cell_width * cm] * num_columns
        , rowHeights = [table_height / num_rows] * num_rows
    )

    table.setStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        , ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        , ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
        , ('FONTSIZE', (0, 0), (-1, -1), font_size)
        , ('GRID', (0, 0), (-1, -1), 0, colors.white)
#        , ('BOX', (0,0), (-1,-1), 0.25, colors.white)
#        , ('INNERGRID', (0,0), (-1,-1), 0.25, colors.white)
    ])
    return table


def create_100seq_table(table_width, font_size, top_row_nums, left_column_nums):
    """
    Create 100 square calculations

    Args:
        table_width: [int | float]
            table width
        font_size: int
            table font size in pt
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
    #table = Table(table_data, colWidths=35, rowHeights=35)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
        ('TOPPADDING', (0, 0), (-1, -1), -10),
    ])
    return table

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
    if(ini.paper_size == 'A4' or ini.paper_size == 'a4'):
        PAPER_SIZE = A4
        PAPER_MARGIN = 30
        HEADER_FONT_SIZE = 14
        TITLE_FONT_SIZE = 24
        SUB_TITLE_FONT_SIZE = 10
        DATE_TIME_FONT_SIZE = 10
        TABLE_WIDTH = 520 - PAPER_MARGIN * mm
        TABLE_HEIGHT = 500
        TABLE_FONT_SIZE = 14
    elif(ini.paper_size == 'B5' or ini.paper_size == 'b5'):
        PAPER_SIZE = B5
        PAPER_MARGIN = 20
        HEADER_FONT_SIZE = 12
        TITLE_FONT_SIZE = 18
        SUB_TITLE_FONT_SIZE = 8
        DATE_TIME_FONT_SIZE = 8
        TABLE_WIDTH = 380 - PAPER_MARGIN * mm
        TABLE_HEIGHT = 410
        TABLE_FONT_SIZE = 12
    try:
        # Create PDF
        OUT_FILENAME = ini.out_file
        doc = SimpleDocTemplate(
            OUT_FILENAME
            , topMargin = PAPER_MARGIN * mm
            , leftMargin = PAPER_MARGIN * mm
            , rightMargin = PAPER_MARGIN * mm
            , bottomMargin = PAPER_MARGIN * mm
            , pagesize = PAPER_SIZE
            , title = TITLE_STR
            , author = AUTHOR
            , subject = SUBJECT
            , creator = AUTHOR
            , producer = AUTHOR
        )
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
        date_time_style = ParagraphStyle(name='DateTime', fontSize=DATE_TIME_FONT_SIZE)
        date = Paragraph(f"<b>{DATE_LABEL}</b> {'_' * 15}", date_time_style)
        time = Paragraph(f"<b>{TIME_LABEL}</b> {'_' * 15}", date_time_style)

        # Combine date and time horizontally
        date_time = Table([[date, time]], colWidths=[5.5 * cm, 5.5 * cm])
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
            date_time, Spacer(1, 40)
        ]

        contents.extend(headers)

        # ------------------------------------------------
        print_type = 100
        print_type = 'ope' # operation
        print_type = 'comp' # complement
        print_type = ini.command
        # ------------------------------------------------

        # table spec
        num_rows = ini.rows
        num_columns = ini.columns
        data_size = num_rows * num_columns

        page = 30

        # Create four operations table
        if print_type == 'ope' or print_type == 'operations':
            for index in range(page):
                nums_a = get_random_nums(data_size, 1, 9)
                nums_b = get_random_nums(data_size, 1, 9)
                operators = ini.operator
                include_number = ini.serial_number
                is_reverse = ini.reverse
                table_height = TABLE_HEIGHT

                if index > 0:
                    contents.extend(headers)

                # get table data
                data = get_four_operation_data(
                    nums_a, nums_b, operators, include_number, is_reverse)

                # create table
                table = create_basic_table(
                    data[0], table_height, TABLE_FONT_SIZE, num_rows, num_columns
                )
                table_w_answer = create_basic_table(
                    data[1], table_height, TABLE_FONT_SIZE, num_rows, num_columns
                )

                contents.append(table)
                contents.append(PageBreak())
#                contents.append(table_w_answer)
#                contents.append(PageBreak())

        # Create 100 seq table
        elif print_type == str(100):
            TABLE_FONT_SIZE = 20
            top_row_nums = get_random_nums(10, 1, 9)
            left_column_nums = get_random_nums(10, 1, 9)
            table = create_100seq_table(
                TABLE_WIDTH
                , TABLE_FONT_SIZE
                , top_row_nums
                , left_column_nums
            )
            table_w_answer = create_100seq_table(
                TABLE_WIDTH
                , TABLE_FONT_SIZE
                , top_row_nums
                , left_column_nums
            )
            contents.append(table)

        # Create complement table
        elif print_type == 'comp' or print_type == 'complements':
            target = 30
            random_nums = get_random_nums(data_size, 1, target - 1)
            data = get_complement_data(random_nums, target)
            table = create_basic_table(
                data[0], TABLE_HEIGHT, TABLE_FONT_SIZE, num_rows, num_columns
            )
            table_w_answer = create_basic_table(
                data[1], TABLE_HEIGHT, TABLE_FONT_SIZE, num_rows, num_columns
            )
            contents.append(table)

        # Build PDF
        doc.build(contents, onFirstPage = addPageNumber, onLaterPages = addPageNumber)

        print("All done")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    args = _init()
    main(args)
