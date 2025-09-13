# 100-Square Calculation Generator

## Overview
This project provides a set of tools to generate various types of mathematical practice worksheets, primarily focusing on 100-square calculations, in PDF format. It's designed to help users create customized practice materials for mental arithmetic and basic math skills.

## Features
*   **Diverse Problem Types**: Generate worksheets for basic arithmetic operations (addition, subtraction, multiplication, division), complements, 100-square calculation tables, multiplication tables (kuku), square numbers, and specific mental arithmetic problems.
*   **Customizable Generation**: Extensive command-line options allow users to specify paper size, number ranges, operators, problem counts, and output formats.
*   **PDF Output**: All worksheets are generated as high-quality PDF files, ready for printing.
*   **Answer Options**: Include answers at the bottom of the page, merge answer files, or output raw problem data to CSV for further analysis.
*   **Automated Batch Generation**: The `factory.sh` script provides an automated way to generate a wide variety of pre-configured worksheets.

## Setup
To use this generator, you need Python 3 and the ReportLab library, along with a LaTeX environment for PDF compilation (though `100masu.py` handles PDF generation directly using ReportLab, `factory.sh` might imply LaTeX for other purposes or older versions).

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ontheroadjp/100-square-calculations.git
    cd 100-square-calculations
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install reportlab
    ```

3.  **(Optional) Install LaTeX environment**: While `100masu.py` uses ReportLab for PDF generation, if you encounter issues or plan to use other LaTeX-based tools, ensure you have a LaTeX distribution (e.g., TeX Live, MiKTeX) with `platex` and `dvipdfmx` installed.

## Usage

### Generating Worksheets with `100masu.py`
The `100masu.py` script is the core generator. You can run it directly with various options.

```bash
python 100masu.py <paper_size> <command> [options]
```

**Example: Generate 5 pages of A4 addition problems**
```bash
python 100masu.py A4 ope -o add -p 5 --out-file addition_A4_5pages.pdf
```

**Example: Generate 100-square calculation table (A3 size)**
```bash
python 100masu.py A3 100 --out-file 100_square_A3.pdf
```

**Example: Generate multiplication table (kuku) for '7' in random order (A4 landscape)**
```bash
python 100masu.py a4l 99 -a 7 --shuffle --out-file kuku_7_random_A4L.pdf
```

For a full list of options, run:
```bash
python 100masu.py -h
```

### Batch Generation with `factory.sh`
The `factory.sh` script automates the generation of a predefined set of worksheets, creating a structured output directory (`dist/`).

```bash
./factory.sh
```

This will generate a variety of mental arithmetic and other practice sheets into the `dist/` directory. Review the `factory.sh` script to understand the specific types and configurations of worksheets it generates.

## Dependencies
*   Python 3
*   ReportLab library (`pip install reportlab`)
*   (Optional) LaTeX environment (for `platex`, `dvipdfmx` if used by other tools or older versions)

## License
MIT License