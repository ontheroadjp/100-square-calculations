# 100 Square Calculations

This Python script generates math calculation practice printouts in PDF format using the ReportLab library. It provides various types of printouts such as arithmetic operations, complements, and a 100 square calculation table.

## Features

- Generate arithmetic operation practice printouts.
- Generate complement practice printouts.
- Generate 100 square calculation practice printouts.
- Command-line interface for easy usage.
- Customizable paper size (A4 or B5).

## Requirements

- Python 3
- ReportLab library

## Usage

1. Clone this repository:
   
   ```bash
   git clone https://github.com/yourusername/math-practice-printouts.git
   ```

2. Navigate to the project directory:
   
   ```bash
   cd math-practice-printouts
   ```

3. Install the required dependencies:
   
   ```bash
   pip install reportlab
   ```

4. Run the script:
   
   ```bash
   python 100masu.py A4 operations
   ```
   
   Replace `A4` with `B5` if you prefer B5 paper size. You can also replace `operations` with `complements` or `100` for different types of printouts.

5. Find the generated PDF file named `result.pdf`.

## Command-line Arguments

- `paper_size`: Choose the paper size (`A4` or `B5`).
- `command`: Choose the type of printout (`operations`, `complements`, or `100`).

## Examples

Generate arithmetic operation practice printouts on A4 paper size:

```bash
python 100masu.py A4 operations
```

Generate complement practice printouts on B5 paper size:

```bash
python 100masu.py B5 complements
```

Generate 100 square calculation practice printouts on B5 paper size:

```bash
python 100masu.py B5 100
```
