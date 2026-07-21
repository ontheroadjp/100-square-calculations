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

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/ontheroadjp/100-square-calculations.git
   ```

2. Navigate to the project directory:

   ```bash
   cd 100-square-calculations
   ```

3. Install the required dependencies:

   ```bash
   pip install reportlab
   ```

## Usage

Run the script:

```bash
python3 100masu.py A4 ope -a 1 -b 1
```

Replace `A4` with `A3`, `B5`, or `a4l` (A4 landscape) if you prefer a different paper size. Replace `ope` with `com`, `100`, `99`, `aBc`, `squ`, or `pi` for a different printout type (see Command-line Arguments below).

Find the generated PDF file named `result.pdf` (and `result_read.pdf` for the answer sheet, unless `--merge` is passed).

For batch-generating a full set of printouts at once, run:

```bash
./factory.sh
```

## Command-line Arguments

- `paper_size`: Choose the paper size (`A3`, `A4`, `B5`, or `a4l` for A4 landscape).
- `command`: Choose the type of printout (`ope` for arithmetic operations, `com` for complements, `100` for the 100-square table, `99` for the multiplication table, `aBc` for the 4-digit mental-math conversion drill, `squ` for square numbers, or `pi` for multiples of pi).

See `python3 100masu.py -h` for the full list of options (digit ranges, operators, rows/columns, answer placement, CSV export, etc.).

> **Known issue:** as of the current `master`, only the `ope` command runs without error. The other commands (`com`, `100`, `99`, `aBc`, `squ`, `pi`) fail with `NameError: name 'ini' is not defined` at `100masu.py:158`. See `docs/L3_implementation/specification_summary.md` for details.

## Examples

Generate arithmetic operation practice printouts on A4 paper size:

```bash
python3 100masu.py A4 ope -a 1 -b 1 -o add
```

Generate multiplication printouts with the mental-math intermediate step on B5 paper size:

```bash
python3 100masu.py B5 ope -a 2 -b 1 -o mul --intermediate
```

## Design Principles

- **Single-purpose CLI, no server/DB.** The tool is a one-shot CLI → ReportLab → PDF/CSV pipeline; there is no network interface, database, or persisted state. See `docs/L0_concept/concept.md` and `docs/L0_concept/policy.md` for the full reasoning.
- **No dependency pinning.** There is no lock file or `requirements.txt`; `reportlab` is installed ad hoc, reflecting this project's scope as a small personal/batch-generation script rather than a deployed service.
- **No automated tests or CI.** Correctness is currently verified by manually running the script and inspecting the generated PDF/CSV output.
