#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
from datetime import datetime
from reportlab.lib.pagesizes import B5, A4, landscape, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer, PageBreak
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
    parser.add_argument('command'
        , choices = ['ope', 'operations', 'comp', 'complements', '100']
        , help = 'To determine what kind of print output'
    )
#    parser.add_argument('paper_type'
#        , default = ''
#        , choices = ['A4', 'B5', 'a4', 'b5']
#        , help = 'Paper size of output PDF'
#    )
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
            List of equations in the format like "a + b = c" or "c = a + b"
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


def get_equation_data(nums_a, nums_b, operators=['+', '-', '*', '/']
                , include_num=False, is_reverse=False):
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
            [0] = no answer, [1] = with answer
    """
    equations = []
    equations_w_answer = []
    print_style = {
        '+': '+'
        , '-': '-'
        , '*': '×'
        , '/': '÷'
    }

    count = 1
    for _ in range(len(nums_a)):
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
                equ = f"{c} = "
                equ_w_answer = f"{c} = {a} {print_style[operator]} {b}"
            else:
                equ = f"{a} {print_style[operator]} {b} = "
                equ_w_answer = f"{a} {print_style[operator]} {b} = {c}"

            if include_num:
                equations.append(str(count) + ' )  ' + equ)
                equations_w_answer.append(str(count) + ' )  ' + equ_w_answer)
            else:
                equations.append(equ)
                equations_w_answer.append(equ_w_answer)

            count += 1

    return [equations, equations_w_answer]


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
        table_data,
        colWidths = [table_width // 11] * 11,
        rowHeights = [table_width // 11] * 11
    )

#    table = Table(
#        table_data,
#        colWidths = [cell_width * cm] * 11,
#        rowHeights = [cell_width * cm] * 11
#    )

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
    header_str = 'Nuts Education'
    title_str = '100 square calculations'
    sub_title_str = 'for Mental Arithmetic'
    date_label = 'Date:'
    time_label = 'Time:'
    if(ini.paper_size == 'A4' or ini.paper_size == 'a4'):
        PAPER_SIZE = A4
        header_font_size = 14
        title_font_size = 24
        sub_title_font_size = 10
        date_time_font_size = 10
        table_width = 500
        table_height = 550
        table_font_size = 14
    elif(ini.paper_size == 'B5' or ini.paper_size == 'b5'):
        PAPER_SIZE = B5
        header_font_size = 12
        title_font_size = 18
        sub_title_font_size = 8
        date_time_font_size = 8
        table_width = 380
        table_height = 410
        table_font_size = 12

    try:
        # Create PDF
        OUT_FILENAME = 'result.pdf'
        doc = SimpleDocTemplate(OUT_FILENAME, pagesize=PAPER_SIZE)

        # Add header
        header_style = ParagraphStyle(
            name='Header', leftIndent=0, fontName='Helvetica'
            , fontSize=header_font_size
        )
        header = Paragraph(f'<b>{header_str}</b>', header_style)

        # Add title
        title_style = ParagraphStyle(
            name='Title', fontName='Helvetica-Bold', fontSize=title_font_size
        )
        title = Paragraph(f'<b>{title_str}</b>', title_style)

        # Add sub title
        sub_title_style = ParagraphStyle(
            name='SubTitle', leftIndent=350, fontName='Helvetica'
            , fontSize=sub_title_font_size
        )
        sub_title = Paragraph(f'<b>{sub_title_str}</b>', sub_title_style)

        # Add date and time
        #now = datetime.now()
        date_time_style = ParagraphStyle(name='DateTime', fontSize=date_time_font_size)
        date = Paragraph(f"<b>{date_label}</b> {'_' * 15}", date_time_style)
        time = Paragraph(f"<b>{time_label}</b> {'_' * 15}", date_time_style)

        # Combine date and time horizontally
        date_time = Table([[date, time]], colWidths=[5.5 * cm, 5.5 * cm])
        date_time.setStyle([
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ])

        # ------------------------------------------------
        print_type = 100
        print_type = 'ope' # operation
        print_type = 'comp' # complement
        print_type = ini.command
        # ------------------------------------------------

        # table spec
        num_rows = 15
        num_columns = 3
        data_size = num_rows * num_columns

        # Create complement table
        if print_type == 'comp' or print_type == 'complements':
            target = 30
            random_nums = get_random_nums(data_size, 1, target - 1)
            data = get_complement_data(random_nums, target)
            table = create_basic_table(
                data[0], table_height, table_font_size, num_rows, num_columns
            )
            table_w_answer = create_basic_table(
                data[1], table_height, table_font_size, num_rows, num_columns
            )

        # Create 100 seq table
        elif print_type == str(100):
            table_font_size = 20
            top_row_nums = get_random_nums(10, 1, 9)
            left_column_nums = get_random_nums(10, 1, 9)
            table = create_100seq_table(
                table_width
                , table_font_size
                , top_row_nums
                , left_column_nums
            )
            table_w_answer = create_100seq_table(
                table_width, cell_width
                , table_font_size
                , top_row_nums
                , left_column_nums
            )

       # Create equations table
        elif print_type == 'ope' or print_type == 'operations':
            nums_a = get_random_nums(data_size, 10, 99)
            nums_b = get_random_nums(data_size, 1, 9)
            operators = ['+', '-', '*', '/']
            operators = ['/']
            include_number = True
            is_reverse = False
            data = get_equation_data(
                nums_a, nums_b, operators, include_number, is_reverse)

            # create table
            table = create_basic_table(
                data[0], table_height, table_font_size, num_rows, num_columns
            )
            table_w_answer = create_basic_table(
                data[1], table_height, table_font_size, num_rows, num_columns
            )

        # Add title, date, time, and table to content
        content = [
            #sub_title, Spacer(1, 10),
            header, Spacer(1, 0),
            title, Spacer(1, 60),
            date_time, Spacer(1, 20),
            table, PageBreak(),
            table_w_answer
        ]

        # Build PDF
        doc.build(content)

        print("All done")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    args = _init()
    main(args)
