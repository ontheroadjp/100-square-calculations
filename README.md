# 100-Square Calculation Generator

## Overview
This project is a tool that automatically generates 100-square calculation practice problems in PDF format.
You can create a specified number of problems for addition, subtraction, or multiplication.

## Features
*   Generates 100-square calculation problems for addition, subtraction, and multiplication
*   Flexible specification of the number of problems to generate
*   Outputs in high-quality PDF format

## How to Use

### 1. Running the Python script (`100masu.py`)

The `100masu.py` script generates TeX files for 100-square calculations.

```bash
python 100masu.py [-n <number_of_problems>] [-o <output_directory>] [-t <calculation_type>]
```

#### Options:
*   `-n`, `--number`: Number of problems to generate (default: 10)
*   `-o`, `--output`: Directory to output TeX files (default: `./`)
*   `-t`, `--type`: Specifies the type of calculation.
    *   `add`: Addition (default)
    *   `sub`: Subtraction
    *   `mul`: Multiplication

#### Example:
To generate 5 addition problems and output them to the `output` directory:
```bash
python 100masu.py -n 5 -o output -t add
```

### 2. Running the Shell script (`factory.sh`)

The `factory.sh` script executes `100masu.py` to generate TeX files, then converts them to PDF using `platex` and `dvipdfmx`.
The generated PDF will be named `result.pdf`.

```bash
./factory.sh
```

#### Example:
```bash
./factory.sh
# This will generate 10 addition 100-square calculation problems and output them as result.pdf.
```

## Operating Environment
*   Python 3
*   LaTeX environment (platex, dvipdfmx)

## License
[Insert license information here]
