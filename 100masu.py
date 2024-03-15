#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm

def _init():
    """
    Initialize argument parser and parse command line arguments.

    Returns:
        args: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s",
        description="Generate a 11x11 (121-cell) table in PDF format with randomly filled numbers.",
        add_help=True,
        epilog="end"
    )
    args = parser.parse_args()
    return args

def main(args):
    """
    Main routine to generate the table and output as PDF.

    Args:
        args: Parsed arguments.
    """
    try:
        # Generate random numbers for top row
        top_row_numbers = list(range(1, 10))
        random.shuffle(top_row_numbers)
        if len(top_row_numbers) < 10:
            top_row_numbers.extend(range(10 - len(top_row_numbers) + 1, 10))
        top_row_numbers = top_row_numbers[:10]

        # Generate random numbers for leftmost column
        left_column_numbers = list(range(1, 10))
        random.shuffle(left_column_numbers)
        if len(left_column_numbers) < 10:
            left_column_numbers.extend(range(10 - len(left_column_numbers) + 1, 10))
        left_column_numbers = left_column_numbers[:10]

        # Create table data
        table_data = [[None] * 12 for _ in range(12)]
        for i in range(10):
            table_data[0][i+1] = top_row_numbers[i]
            table_data[i+1][0] = left_column_numbers[i]
        table_data[11][0] = left_column_numbers[9]
        table_data[0][11] = top_row_numbers[9]

        # Create PDF
        doc = SimpleDocTemplate("result.pdf", pagesize=A4)

        # Add title
        title_style = ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=24)
        title = Paragraph("<b>100 square calculations</b>", title_style)

        # Add date and time
        now = datetime.now()
        date_time_style = ParagraphStyle(name='DateTime', fontSize=12)
        date = Paragraph(f"<u>Date:</u> {'_' * 15}", date_time_style)
        time = Paragraph(f"<u>Time:</u> {'_' * 15}", date_time_style)

        # Create table
        # Create table
        table = Table(table_data, colWidths=[1.2 * cm] * 12, rowHeights=[1.2 * cm] * 12)  # 修正箇所: 幅と高さを2cmに変更
        #table = Table(table_data, colWidths=35, rowHeights=35)
        table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ])

        # Add title, date, time, and table to content
        content = [title, Spacer(1, 40), date, Spacer(1, 20), time, Spacer(1, 20), table]

        # Build PDF
        doc.build(content)

        print("All done")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    args = _init()
    main(args)
