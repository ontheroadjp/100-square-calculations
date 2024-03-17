#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, landscape, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm

def _init():
    """
    Initialize argument parser and parse command line arguments.

    Returns:
        args: argparse object
            Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s A4 | B5",
        description="Outputs math calculation practice printouts",
        add_help=True,
        epilog="end"
    )
    parser.add_argument('paper_size'
        , default = 'A4'
        , choices = ['A4', 'B5', 'a4', 'b5']
        , help = 'Paper size of output PDF'
    )
#    parser.add_argument('paper_type'
#        , default = ''
#        , choices = ['A4', 'B5', 'a4', 'b5']
#        , help = 'Paper size of output PDF'
#    )
    args = parser.parse_args()
    return args

def get_random_num_list(num=10, min=1, max=9):
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
    random_num = []
    for i in range(num):
        random_num.append(random.choice(min_max_list))
    return random_num


def get_complement_list(nums_a, target=100, include_num=False, include_answer=False):
    """
    Create complement from target of nums_s

    Args:
        nums_a: list
            List of seed numbers for using develop complemention
        include_number: bool, optional
            Whether to include the number before the complemention (default is False)
        include_answer: bool, optional
            Whether to include the answer in the complemention (default is True)

    Returns:
        complements: list
            List of equations in the format like "a + b = c" or "c = a + b"
    """
    complements = []
    count = 1
    for num in nums_a:
        if include_answer:
            c = 100 - num
            comp = f"{num} => {c}"
        else:
            comp = f"{num} =>"


        if include_num:
            complements.append(str(count) + ') ' + comp)
        else:
            complements.append(comp)

        count += 1
    return complements


def get_equation_list(nums_a, nums_b, operators=['+', '-', '*', '/']
                , include_num=False, include_answer=True, is_reverse=False):
    """
    Create equations from num_a and num_b.

    Args:
        nums_a: list
            List of seed numbers for using develop equations
        nums_b: list
            List of seed numbers for using develop equations
        include_number: bool, optional
            Whether to include the number before the equations (default is False)
        include_answer: bool, optional
            Whether to include the answer in the equations (default is True)
        is_reverse: bool, optional
            Output equations reversed (default is False)

    Returns:
        equations: list
            List of equations in the format like "a + b = c" or "c = a + b"
    """
    equations = []
    print_operations = {
        '+': '+'
        , '-': '-'
        , '*': '×'
        , '/': '÷'
    }

    count = 1
    for _ in range(len(nums_a)):
        random.shuffle(operators)
#        random.shuffle(nums_a)
#        random.shuffle(nums_b)
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
                equation = f"{c} = "
                if include_answer:
                    equation += f"{a} " + print_operations[operator] + f" {b}"
            else:
                equation = f"{a} " + print_operations[operator] + f" {b} = "
                if include_answer:
                    equation += f"{c}"

            if include_num:
                equations.append(str(count) + ') ' + equation)
            else:
                equations.append(equation)

            count += 1

    return equations


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
#    # Calculate table cell size
#    # PAPER_SIZE[0] converts from inch to mm to cm
#    padding_left = 0
#    padding_right = 0
#    table_width = (PAPER_SIZE[0] * 0.39371 / 10 - padding_left - padding_right)
#    cell_width = table_width / num_columns
#    colWidths = [cell_width] * num_columns,

    # insert table data
    rows = [data_list[i*num_columns:(i+1)*num_columns] for i in range(num_rows)]
#    table_data = [[Paragraph(cell, ParagraphStyle(name='Equation', fontName='Helvetica', fontSize=font_size, keepWithNext=True)) for cell in row] for row in rows]
    table_data = []
    for row in rows:
        # 行の各セルを段落オブジェクトに変換し、リストに追加
        paragraph_row = []
        for cell in row:
            paragraph = Paragraph(cell, ParagraphStyle(
                                            name='Equation'
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
        #        , ('FONT',(0,0),(-1,1),'Times-Bold',10,12)
        #        , ('FONT',(0,1),(-1,-1),'Courier',8,8)
        , ('GRID', (0, 0), (-1, -1), 0, colors.white)
#        , ('BOX', (0,0), (-1,-1), 0.25, colors.white)
#        , ('INNERGRID', (0,0), (-1,-1), 0.25, colors.white)
    ])
    return table


def create_100seq_table(cell_width, font_size, top_row_numbers, left_column_numbers):
    """
    Create 100 square calculations

    Args:
        cell_width: [int | float]
            table cell size in cm
        font_size: int
            table font size in pt
        top_row_numbers: list
            numbers for top row as list type
        left_column_numbers: list
            numbers for column as list type

    Returns:
        table: table object
            100 sequare table object for PDF
    """
    table_data = [[None] * 11 for _ in range(11)]
    for i in range(10):
        table_data[0][i+1] = top_row_numbers[i]
        table_data[i+1][0] = left_column_numbers[i]

    # Create table
    table = Table(
        table_data,
        colWidths = [cell_width * cm] * 11,
        rowHeights = [cell_width * cm] * 11
    )
    #table = Table(table_data, colWidths=35, rowHeights=35)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
    ])
    return table


def main(ini):
    """
    Main routine to generate the table and output as PDF.

    Args:
        args: argparse object
            Parsed arguments.
    """

    try:
        # Create PDF
        if(ini.paper_size == 'A4'):
            PAPER_SIZE = A4
        elif(ini.paper_size == 'a4'):
            PAPER_SIZE = A4
        elif(ini.paper_size == 'B5'):
            PAPER_SIZE = B5
        elif(ini.paper_size == 'b5'):
            PAPER_SIZE = B5

        OUT_FILENAME = 'result.pdf'
        doc = SimpleDocTemplate(OUT_FILENAME, pagesize=PAPER_SIZE)

        # Add header
        HEADER = 'Nuts Education'
        header_style = ParagraphStyle(
            name='Header', leftIndent=0, fontName='Helvetica', fontSize=12
        )
        header = Paragraph('<b>' + HEADER + '</b>', header_style)

        # Add title
        TITLE = '100 square calculations'
        title_style = ParagraphStyle(
            name='Title', fontName='Helvetica-Bold', fontSize=24
        )
        title = Paragraph('<b>' + TITLE + '</b>', title_style)

        # Add sub title
        SUB_TITLE = 'for Mental Arithmetic'
        sub_title_style = ParagraphStyle(
            name='SubTitle', leftIndent=350, fontName='Helvetica', fontSize=10
        )
        sub_title = Paragraph('<b>' + SUB_TITLE + '</b>', sub_title_style)

        # Add date and time
        #now = datetime.now()
        date_time_style = ParagraphStyle(name='DateTime', fontSize=10)
        date = Paragraph(f"<b>Date:</b> {'_' * 15}", date_time_style)
        time = Paragraph(f"<b>Time:</b> {'_' * 15}", date_time_style)
        #time = Paragraph(f"<u>Time:</u> {'_' * 15}", date_time_style) # w/underline

        # Combine date and time horizontally
        date_time = Table([[date, time]], colWidths=[5.5 * cm, 5.5 * cm])
        date_time.setStyle([
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ])

        # ------------------------------------------------
        print_type = 100
        print_type = 10
        print_type = 'comp'
        # ------------------------------------------------

        # Create complement table
        if print_type == 'comp':
            if(PAPER_SIZE == A4):
                table_height = 550
                font_size = 14
            elif(PAPER_SIZE == B5):
                table_height = 410
                font_size = 12
            num_rows = 10
            num_columns = 4
            nums = get_random_num_list(num_rows * num_columns, 1, 99)
            comps = get_complement_list(nums, include_answer=False)
            comp_table = create_basic_table(
                comps, table_height, font_size, num_rows, num_columns
            )

        # Create 100 seq table
        if print_type == 100:
            cell_width = 1.2
            font_size = 20
            top_row_numbers = get_random_num_list(10, 1, 9)
            left_column_numbers = get_random_num_list(10, 1, 9)
            table = create_100seq_table(
                cell_width
                , font_size
                , top_row_numbers
                , left_column_numbers
            )

       # Create equations table
        if print_type == 10:
            # table spec
            if(PAPER_SIZE == A4):
                table_height = 550
                font_size = 14
            elif(PAPER_SIZE == B5):
                table_height = 410
                font_size = 12
            num_rows = 10
            num_columns = 4

            # get equations
            num = num_rows * num_columns
            nums_a = get_random_num_list(num, 10, 99)
            nums_b = get_random_num_list(num, 1, 9)
            operators = ['+', '-', '*', '/']
            operators = ['/']
            include_number = False
            include_answer = True
            is_reverse = False
            equations = get_equation_list(
                nums_a, nums_b, operators, include_number, include_answer, is_reverse)

            # create table
            table = create_basic_table(
                equations, table_height, font_size, num_rows, num_columns
            )

        # Add title, date, time, and table to content
        content = [
            #sub_title, Spacer(1, 10),
            header, Spacer(1, 0),
            title, Spacer(1, 60),
            date_time, Spacer(1, 20),
#            table
            comp_table
        ]

        # Build PDF
        doc.build(content)

        print("All done")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    args = _init()
    main(args)
