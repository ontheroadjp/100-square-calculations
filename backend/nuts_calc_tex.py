#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nuts_calc_tex.py -- Phase 1 CLI/PDF foundation (issue #20) + Phase 2 `ope`
command (issue #21) + Phase 3 `com` command (issue #22) + Phase 4 `100`
command (issue #23) + Phase 5 `99` command (issue #24) + Phase 6 `aBc`
command (issue #25) + Phase 7 `squ` command (issue #26) + Phase 8 `pi`
command (issue #27).

A 100%-LaTeX-rendered, fully independent reimplementation of nuts_calc.py's
CLI surface (see the tracking issue #19). This file has zero code
dependency on nuts_calc.py: no imports, no shared modules -- the two are
meant to run side by side, each self-contained.

`ope` (horizontal and --vertical, all operators plus mix, --intermediate),
`com` (complement-to-target), `100` (100-square addition table), `99`
(times-table / kuku, with --descend/--reverse/--shuffle ordering), `aBc`
(mental-arithmetic digit-pair conversion), `squ` (square numbers, with
--descend/--reverse/--shuffle ordering), and `pi` (multiplication by pi,
with the same --descend/--reverse/--shuffle ordering) are all implemented.

Requires a LaTeX distribution (`pdflatex`) on PATH. The `longdivision`
CTAN package (used by `ope --vertical -o div`) is vendored into this repo
under `vendor/texmf/` and located via TEXINPUTS, so no manual TeX package
installation is required beyond a base LaTeX distribution that also
includes `xlop` (e.g. `texlive-latex-base` + `texlive-latex-extra`).
"""

import argparse
import csv
import os
import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Literal, TypeVar


MIN_ROWS_OR_COLUMNS = 1
DEFAULT_ROWS = 10
PAGE_SIDE_MARGIN_MM = 15
PAGE_TOP_MARGIN_MM = 20
PAGE_BOTTOM_MARGIN_MM = 40
FOOTER_TEXT_LOWERING_MM = 20
VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE = {
    'a3': 4,
    'a4': 4,
    'b5': 2,
    'a4l': 2,
}
ROW_VSPACE_EM = 2.0
MAX_OPERAND_RETRY_ATTEMPTS = 1000
TERM_COUNT_FLOOR_DEFAULT = 2
TERM_COUNT_FLOOR_PARENTHESES = 3
MAX_OPE_TERMS = 12
INTERMEDIATE_SINGLE_DIGIT_MAX = 9
MIN_COMPLEMENT_TARGET = 2
ABC_DIGIT_MAX = 9
TABCOLSEP_COUNT_PER_COLUMN = 2
MAX_HUNDRED_SQUARE_DIGITS = 3
HUNDRED_SQUARE_SIZE = 10
HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR = 2
HUNDRED_SQUARE_HEADER_COLOR = 'lightgray'
PI_MULTIPLIER = 3.14
MIN_FRACTION_DIGITS = 1
MAX_FRACTION_DIGITS = 3
BLANK_ANSWER_TEX = '\\hspace{1.5em}'
BOXED_BLANK_TEX = '\\vcenter{\\hbox{\\fbox{\\rule{0pt}{1em}\\hspace{1em}}}}'
MIN_DECIMAL_PLACES = 0
MAX_DECIMAL_PLACES = 2
MIXED_OPERAND_KINDS = ('int', 'decimal', 'fraction')
BORROWING_MINUENDS = tuple(range(10, 20))
BORROWING_SUBTRAHENDS = tuple(range(1, 10))

CarryMode = Literal['required', 'none', 'mixed']
RemainderMode = Literal['required', 'none', 'mixed']

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_TEXMF_DIR = os.path.join(SCRIPT_DIR, 'vendor', 'texmf')

OPERATOR_TEX_SYMBOLS = {'add': '+', 'sub': '-', 'mul': '\\times', 'div': '\\div'}
MIX_OPERATORS = ['add', 'sub', 'mul', 'div']
XLOP_VERTICAL_COMMANDS = {'add': 'opadd', 'sub': 'opsub', 'mul': 'opmul'}
XLOP_VERTICAL_LAYOUT_OPTIONS = 'voperator=bottom,columnwidth=2ex'

PAPER_SIZE_TO_GEOMETRY_OPTION = {
    'a3': 'a3paper',
    'a4': 'a4paper',
    'b5': 'b5paper',
    'a4l': 'a4paper,landscape',
}

HEADER_STR = 'Nuts Education'
TITLE_STR = '100 square calculations'
SUB_TITLE_STR = 'for Mental Arithmetic'
COPYRIGHT_STR = 'Copyright(c) 2024 Nuts Education'


def failure(message: str) -> None:
    print(message)
    exit(1)


def _init() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Defined independently of nuts_calc.py's `_init()` (no shared code), but
    mirrors its flag surface for a familiar CLI. `command`/`operator` are
    fully dispatched on for `ope`, `com`, `100`, `99`, `aBc`, `squ`, and
    `pi`.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s A4 | B5",
        description="""
            LaTeX-rendered calculation practice printout generator
            (independent reimplementation of nuts_calc.py).
        """,
        add_help=True,
        allow_abbrev=False,
        epilog="end"
    )
    parser.add_argument('paper_size'
        , type = str
        , choices = ['A3', 'A4', 'B5', 'a3', 'a4', 'b5', 'a4l']
        , help = 'Paper size of prints to be output'
    )
    parser.add_argument('command'
        , type = str
        , choices = ['ope', 'com', '100', '99', 'aBc', 'squ', 'pi', 'frac', 'mixed', 'compare']
        , help = 'Type of formula to output (including "frac" for fraction arithmetic, "compare" for fraction comparison, and "mixed" for int/decimal/fraction arithmetic)'
    )
    parser.add_argument('-a', '--a-value'
        , type = int
        , help = 'Number of digits in the first term of the formula'
    )
    parser.add_argument('-b', '--b-value'
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
    carry_group = parser.add_mutually_exclusive_group()
    carry_group.add_argument('--carry-borrow'
        , dest = 'carry_mode'
        , action = 'store_const'
        , const = 'required'
        , default = None
        , help = 'Require carrying in addition or borrowing in subtraction (two-term ope add/sub only)'
    )
    carry_group.add_argument('--no-carry-borrow'
        , dest = 'carry_mode'
        , action = 'store_const'
        , const = 'none'
        , help = 'Require no carrying in addition and no borrowing in subtraction (two-term ope add/sub only)'
    )
    carry_group.add_argument('--mixed-carry-borrow'
        , dest = 'carry_mode'
        , action = 'store_const'
        , const = 'mixed'
        , help = 'Mix addition/subtraction with and without carrying/borrowing (two-term ope -o add sub only)'
    )
    remainder_group = parser.add_mutually_exclusive_group()
    remainder_group.add_argument('--remainder'
        , dest = 'remainder_mode'
        , action = 'store_const'
        , const = 'required'
        , default = None
        , help = 'Require a nonzero remainder (ope -o div only)'
    )
    remainder_group.add_argument('--no-remainder'
        , dest = 'remainder_mode'
        , action = 'store_const'
        , const = 'none'
        , help = 'Require exact (no-remainder) division (ope -o div only; same as the default)'
    )
    remainder_group.add_argument('--mixed-remainder'
        , dest = 'remainder_mode'
        , action = 'store_const'
        , const = 'mixed'
        , help = 'Mix exact and remainder division (ope -o div only)'
    )
    parser.add_argument('--numerator-digits'
        , type = int
        , default = 1
        , help = 'Number of digits in fraction numerators (frac, compare, mixed)'
    )
    parser.add_argument('--denominator-digits'
        , type = int
        , default = 1
        , help = 'Number of digits in fraction denominators (frac, compare, mixed)'
    )
    parser.add_argument('--same-denominator'
        , default = False
        , action = 'store_true'
        , help = 'Use the same denominator for both fraction operands (frac only)'
    )
    parser.add_argument('--different-denominators'
        , default = False
        , action = 'store_true'
        , help = 'Require different denominators for the two fraction operands (frac only)'
    )
    parser.add_argument('--proper-operands'
        , default = False
        , action = 'store_true'
        , help = 'Use proper fractions for both operands (frac only)'
    )
    parser.add_argument('--proper-result'
        , default = False
        , action = 'store_true'
        , help = 'Only generate positive proper-fraction answers (frac only)'
    )
    parser.add_argument('--comparison-pattern'
        , choices = ['same-denominator', 'same-numerator', 'different-denominators']
        , default = 'different-denominators'
        , help = 'Fraction comparison pattern (compare only)'
    )
    parser.add_argument('--a-fraction-form'
        , choices = ['proper', 'improper', 'mixed', 'mix']
        , default = 'proper'
        , help = 'Form of the left comparison operand (compare only; mix chooses per problem)'
    )
    parser.add_argument('--b-fraction-form'
        , choices = ['proper', 'improper', 'mixed', 'mix']
        , default = 'proper'
        , help = 'Form of the right comparison operand (compare only; mix chooses per problem)'
    )
    parser.add_argument('--a-decimal-places'
        , type = int
        , default = MIN_DECIMAL_PLACES
        , help = (
            f'Number of digits after the decimal point for the first "ope" '
            f'operand (0-{MAX_DECIMAL_PLACES}, ope only). The operand range '
            '(-a/--a-min/--a-max) is interpreted as a scaled integer and '
            'divided by 10^places for display, so the result is always an '
            'exact, finite decimal (no floating point involved).'
        )
    )
    parser.add_argument('--b-decimal-places'
        , type = int
        , default = MIN_DECIMAL_PLACES
        , help = 'Number of digits after the decimal point for the second "ope" operand (0-%d, ope only)' % MAX_DECIMAL_PLACES
    )
    parser.add_argument('--decimal-places'
        , type = int
        , default = 1
        , help = (
            f'Number of digits after the decimal point used for '
            f'decimal-kind operands (0-{MAX_DECIMAL_PLACES}, mixed only)'
        )
    )
    parser.add_argument('--a-kind'
        , default = list(MIXED_OPERAND_KINDS)
        , choices = list(MIXED_OPERAND_KINDS)
        , nargs = '*'
        , help = 'Allowed operand kinds for the first "mixed" term, chosen per problem (mixed only)'
    )
    parser.add_argument('--b-kind'
        , default = list(MIXED_OPERAND_KINDS)
        , choices = list(MIXED_OPERAND_KINDS)
        , nargs = '*'
        , help = 'Allowed operand kinds for the second and later "mixed" terms, chosen per problem (mixed only)'
    )
    parser.add_argument('--descend'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in descending order'
    )
    parser.add_argument('--reverse'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in reverse order'
    )
    parser.add_argument('--shuffle'
        , default = False
        , action = 'store_true'
        , help = 'Multiplication table in random order'
    )
    parser.add_argument('--intermediate'
        , default = False
        , action = 'store_true'
        , help = 'Write an intermediate formula'
    )
    parser.add_argument('--vertical'
        , default = False
        , action = 'store_true'
        , help = 'Output "ope" problems in vertical (written-calculation, hissan) format'
    )
    parser.add_argument('--terms'
        , type = int
        , default = None
        , help = (
            'Exact number of terms (operands) per "ope" problem, e.g. 4 for '
            '"a op b op c op d". Overrides --terms-min/--terms-max. Clamped '
            f'to [{TERM_COUNT_FLOOR_DEFAULT}, {MAX_OPE_TERMS}] '
            f'(or [{TERM_COUNT_FLOOR_PARENTHESES}, {MAX_OPE_TERMS}] with '
            '--use-parentheses) instead of erroring'
        )
    )
    parser.add_argument('--terms-min'
        , type = int
        , default = TERM_COUNT_FLOOR_DEFAULT
        , help = 'Minimum number of terms per "ope" problem (each problem draws its own random count)'
    )
    parser.add_argument('--terms-max'
        , type = int
        , default = TERM_COUNT_FLOOR_DEFAULT
        , help = 'Maximum number of terms per "ope" problem (each problem draws its own random count)'
    )
    parser.add_argument('--mixed-operators'
        , default = False
        , action = 'store_true'
        , help = (
            'Choose an independent operator per gap/node instead of one '
            'operator for the whole "ope" problem; flat expressions are '
            'evaluated with standard operator precedence (* / before + -)'
        )
    )
    parser.add_argument('--use-parentheses'
        , default = False
        , action = 'store_true'
        , help = (
            'Output "ope" problems as parenthesized N-term (N>=3) expressions '
            'using a random binary expression tree; -o/--operator (including '
            '"mix") is chosen per node (or once per problem without '
            '--mixed-operators)'
        )
    )
    parser.add_argument('--missing-value'
        , default = False
        , action = 'store_true'
        , help = (
            'Output "ope" problems as missing-number (mushikuizan) expressions '
            '"a op b = c" with one of a/b boxed out; the blanked operand is '
            'chosen per problem'
        )
    )
    parser.add_argument('-r', '--rows'
        , type = int
        , default = None
        , help = 'Lines of question per page'
    )
    parser.add_argument('-c', '--columns'
        , type = int
        , default = 2
        , help = 'Number of columns of questions per page'
    )
    parser.add_argument('-ww', '--with-bottom-answer'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to post answers at the bottom of the page'
    )
    parser.add_argument('-p', '--page'
        , type = int
        , default = 1
        , help = 'Number of pages included in the output file'
    )
    parser.add_argument('-m', '--merge'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to merge the answer pages into the same PDF'
    )
    parser.add_argument('--csv'
        , default = False
        , action = 'store_true'
        , help = 'Flag whether or not to output csv raw data'
    )
    parser.add_argument('--out-file'
        , default = 'result.pdf'
        , help = 'Output file path'
    )
    parser.add_argument('--debug'
        , default = False
        , action = 'store_true'
        , help = 'Enable debug mode'
    )
    args = parser.parse_args()

    if args.rows is None:
        if args.command == 'ope' and args.vertical:
            args.rows = VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE[args.paper_size.lower()]
        else:
            args.rows = DEFAULT_ROWS

    def set_min_max_value(value: int) -> list[int]:
        digits_list = ((1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999))
        min_val, max_val = digits_list[value - 1]
        return [min_val, max_val]

    if args.command == '100':
        # Validated before set_min_max_value() is called below: that function
        # indexes digits_list with value - 1 and raises an unhandled
        # IndexError for value > 5, and silently wraps around to the wrong
        # (5-digit) range for value <= 0 (negative indexing) -- both must be
        # rejected with a clean CLI error first.
        if (args.a_value is not None and not 1 <= args.a_value <= MAX_HUNDRED_SQUARE_DIGITS) \
                or (args.b_value is not None and not 1 <= args.b_value <= MAX_HUNDRED_SQUARE_DIGITS):
            failure(
                f"-a/--a-value and -b/--b-value must be between 1 and "
                f"{MAX_HUNDRED_SQUARE_DIGITS} digits for the '100' command."
            )

    if args.command in ('ope', '100'):
        if args.a_value is not None:
            args.a_min, args.a_max = set_min_max_value(args.a_value)
        if args.b_value is not None:
            args.b_min, args.b_max = set_min_max_value(args.b_value)

    if args.rows < MIN_ROWS_OR_COLUMNS or args.columns < MIN_ROWS_OR_COLUMNS:
        failure(f"-r/--rows and -c/--columns must be at least {MIN_ROWS_OR_COLUMNS}.")

    if args.page < 1:
        failure("-p/--page must be at least 1.")

    if args.command == 'com':
        if args.a_value is None:
            failure("-a/--a-value (complement target) is required for the 'com' command.")
        if args.a_value < MIN_COMPLEMENT_TARGET:
            failure(f"-a/--a-value (complement target) must be at least {MIN_COMPLEMENT_TARGET} for the 'com' command.")

    if args.command == '99':
        if args.a_value is None:
            failure("-a/--a-value (times-table row) is required for the '99' command.")

    if args.command == 'squ':
        if args.a_value is None:
            failure("-a/--a-value (starting square number) is required for the 'squ' command.")

    if args.command == 'pi':
        if args.a_value is None:
            failure("-a/--a-value (starting multiplicand) is required for the 'pi' command.")

    if args.command in ('frac', 'compare', 'mixed'):
        # All three commands create fraction operands; the digit options are
        # shared so comparison worksheets can use the same familiar controls.
        for option_name, value in (
            ('--numerator-digits', args.numerator_digits),
            ('--denominator-digits', args.denominator_digits),
        ):
            if not MIN_FRACTION_DIGITS <= value <= MAX_FRACTION_DIGITS:
                failure(
                    f"{option_name} must be between {MIN_FRACTION_DIGITS} "
                    f"and {MAX_FRACTION_DIGITS} for the '{args.command}' command."
                )

    if args.command == 'frac':
        if args.same_denominator and args.different_denominators:
            failure("--same-denominator and --different-denominators cannot be combined.")
        if args.proper_operands and args.numerator_digits > args.denominator_digits:
            failure(
                "--proper-operands requires --numerator-digits to be no greater "
                "than --denominator-digits."
            )

    fraction_arithmetic_options_given = (
        args.same_denominator or args.different_denominators
        or args.proper_operands or args.proper_result
    )
    if args.command != 'frac' and fraction_arithmetic_options_given:
        failure("--same-denominator/--different-denominators/--proper-operands/--proper-result are only supported for the 'frac' command.")

    comparison_options_given = (
        args.comparison_pattern != 'different-denominators'
        or args.a_fraction_form != 'proper' or args.b_fraction_form != 'proper'
    )
    if args.command != 'compare' and comparison_options_given:
        failure("--comparison-pattern/--a-fraction-form/--b-fraction-form are only supported for the 'compare' command.")

    if args.intermediate:
        if args.command != 'ope':
            failure("--intermediate is only supported for the 'ope' command.")
        if args.vertical:
            failure("--intermediate cannot be combined with --vertical.")
        if args.operator != ['mul']:
            failure("--intermediate only supports a single 'mul' operator (use -o mul).")
        if args.b_max > INTERMEDIATE_SINGLE_DIGIT_MAX:
            failure("--intermediate only supports a single-digit second operand (use -b 1 or --b-max <= 9).")

    if args.use_parentheses:
        if args.command != 'ope':
            failure("--use-parentheses is only supported for the 'ope' command.")
        if args.vertical:
            failure("--use-parentheses cannot be combined with --vertical.")
        if args.intermediate:
            failure("--use-parentheses cannot be combined with --intermediate.")

    if args.missing_value:
        if args.command != 'ope':
            failure("--missing-value is only supported for the 'ope' command.")
        if args.vertical:
            failure("--missing-value cannot be combined with --vertical.")
        if args.intermediate:
            failure("--missing-value cannot be combined with --intermediate.")
        if args.use_parentheses:
            failure("--missing-value cannot be combined with --use-parentheses.")

    if args.terms is not None:
        # Overrides --terms-min/--terms-max unconditionally, mirroring how
        # -a/--a-value overrides --a-min/--a-max above (not a rejected
        # combination -- the exact-value form simply wins).
        args.terms_min = args.terms_max = args.terms

    terms_options_given = (
        args.terms is not None or args.terms_min != TERM_COUNT_FLOOR_DEFAULT
        or args.terms_max != TERM_COUNT_FLOOR_DEFAULT or args.mixed_operators
    )
    if terms_options_given and args.command not in ('ope', 'mixed'):
        failure("--terms/--terms-min/--terms-max/--mixed-operators are only supported for the 'ope' and 'mixed' commands.")

    if args.command == 'ope' and terms_options_given:
        if args.terms_min > args.terms_max:
            failure("--terms-min must be less than or equal to --terms-max.")
        if args.vertical:
            failure("--terms/--terms-min/--terms-max/--mixed-operators cannot be combined with --vertical.")
        if args.intermediate:
            failure("--terms/--terms-min/--terms-max/--mixed-operators cannot be combined with --intermediate.")
        if args.missing_value:
            failure("--terms/--terms-min/--terms-max/--mixed-operators cannot be combined with --missing-value.")

    if args.carry_mode is not None:
        allowed_carry_operators = {'add', 'sub'}
        if (
                args.command != 'ope' or not args.operator
                or not set(args.operator) <= allowed_carry_operators
            ):
            failure("--carry-borrow/--no-carry-borrow/--mixed-carry-borrow only support two-term 'ope' add/sub operators.")
        if args.carry_mode == 'mixed' and set(args.operator) != allowed_carry_operators:
            failure("--mixed-carry-borrow requires both addition and subtraction (use -o add sub).")
        if args.use_parentheses or args.missing_value or terms_options_given:
            failure(
                "--carry-borrow/--no-carry-borrow/--mixed-carry-borrow cannot be combined with "
                "--use-parentheses/--missing-value/--terms family."
            )
        if args.a_decimal_places != MIN_DECIMAL_PLACES or args.b_decimal_places != MIN_DECIMAL_PLACES:
            failure("--carry-borrow/--no-carry-borrow/--mixed-carry-borrow only support integer operands.")

    if args.remainder_mode is not None:
        if args.command != 'ope' or args.operator != ['div']:
            failure("--remainder/--no-remainder/--mixed-remainder only support 'ope -o div'.")
        if args.use_parentheses or args.missing_value or terms_options_given:
            failure(
                "--remainder/--no-remainder/--mixed-remainder cannot be combined with "
                "--use-parentheses/--missing-value/--terms family."
            )
        if args.a_decimal_places != MIN_DECIMAL_PLACES or args.b_decimal_places != MIN_DECIMAL_PLACES:
            failure("--remainder/--no-remainder/--mixed-remainder only support integer operands.")

    if args.command == 'mixed' and terms_options_given and args.terms_min > args.terms_max:
        failure("--terms-min must be less than or equal to --terms-max.")

    if args.command in ('ope', 'mixed'):
        args.terms_min, args.terms_max = resolve_term_range(
            args.terms_min, args.terms_max, args.use_parentheses,
        )

    if args.a_decimal_places != MIN_DECIMAL_PLACES or args.b_decimal_places != MIN_DECIMAL_PLACES:
        if args.command != 'ope':
            failure("--a-decimal-places/--b-decimal-places are only supported for the 'ope' command.")
        for option_name, value in (
            ('--a-decimal-places', args.a_decimal_places),
            ('--b-decimal-places', args.b_decimal_places),
        ):
            if not MIN_DECIMAL_PLACES <= value <= MAX_DECIMAL_PLACES:
                failure(f"{option_name} must be between {MIN_DECIMAL_PLACES} and {MAX_DECIMAL_PLACES}.")
        if args.vertical:
            failure("--a-decimal-places/--b-decimal-places cannot be combined with --vertical.")
        if args.intermediate:
            failure("--a-decimal-places/--b-decimal-places cannot be combined with --intermediate.")
        if args.use_parentheses or args.missing_value or terms_options_given:
            failure(
                "--a-decimal-places/--b-decimal-places cannot be combined with "
                "--use-parentheses/--missing-value/--terms family."
            )
        if args.a_decimal_places != args.b_decimal_places and args.operator not in (['mul'], ['div']):
            failure(
                "When --a-decimal-places and --b-decimal-places differ, "
                "-o/--operator must be exactly 'mul' or exactly 'div' "
                "(decimal-by-integer multiplication/division)."
            )
        if 'div' in args.operator and args.a_decimal_places < args.b_decimal_places:
            failure(
                "--a-decimal-places must be greater than or equal to "
                "--b-decimal-places when dividing (the quotient's decimal "
                "places are a_decimal_places - b_decimal_places, which must "
                "not be negative)."
            )

    mixed_only_options_given = (
        args.decimal_places != 1
        or args.a_kind != list(MIXED_OPERAND_KINDS)
        or args.b_kind != list(MIXED_OPERAND_KINDS)
    )
    if args.command == 'mixed':
        if not MIN_DECIMAL_PLACES <= args.decimal_places <= MAX_DECIMAL_PLACES:
            failure(f"--decimal-places must be between {MIN_DECIMAL_PLACES} and {MAX_DECIMAL_PLACES} for the 'mixed' command.")
    elif mixed_only_options_given:
        failure("--decimal-places/--a-kind/--b-kind are only supported for the 'mixed' command.")

    return args


def resolve_term_range(terms_min: int, terms_max: int, use_parentheses: bool) -> tuple[int, int]:
    """
    Clamp a requested (terms_min, terms_max) range to the applicable
    floor/ceiling instead of rejecting it.

    Deliberate, explicit exception to this file's dominant failure()/
    exit(1) validation convention (see docs/L3_implementation/
    nuts_calc_tex.py.md): a requested term count at or below the floor is
    silently clamped up rather than rejected, since fewer than 2 terms is
    meaningless for any "ope" expression and fewer than 3 is meaningless
    for --use-parentheses (grouping only two terms). MAX_OPE_TERMS is a
    practical ceiling to keep print layout and sub/div-chain retry odds
    from degrading without bound. Assumes terms_min <= terms_max on input
    (validated by the caller before clamping); clamping each bound
    independently with the same floor/ceiling preserves that ordering.
    """
    floor = TERM_COUNT_FLOOR_PARENTHESES if use_parentheses else TERM_COUNT_FLOOR_DEFAULT
    return (
        min(max(terms_min, floor), MAX_OPE_TERMS),
        min(max(terms_max, floor), MAX_OPE_TERMS),
    )


@dataclass
class Page:
    """
    One page's worth of renderable LaTeX content.

    Attributes:
        blocks: One LaTeX snippet per problem, laid out `columns`-wide.
        columns: Number of columns to arrange `blocks` into.
        bottom_answer_tex: Optional LaTeX snippet appended near the page
            bottom (e.g. a compact answer-key line); `None` to omit it.
        layout: 'inline' (a full-width grid for horizontal-format problems),
            'tabular' (a LaTeX tabular grid with one block per cell, used by
            --vertical hissan blocks so multi-row blocks like
            xlop/longdivision output stay column-aligned), or 'block' (one
            self-contained LaTeX block, used by the 100-square table).
    """
    blocks: list[str] = field(default_factory=list)
    columns: int = 1
    bottom_answer_tex: str | None = None
    layout: str = 'inline'


def build_preamble_tex(paper_size: str) -> str:
    geometry_option = PAPER_SIZE_TO_GEOMETRY_OPTION[paper_size.lower()]
    return (
        "\\documentclass[12pt]{article}\n"
        f"\\usepackage[{geometry_option},margin={PAGE_SIDE_MARGIN_MM}mm,top={PAGE_TOP_MARGIN_MM}mm,"
        f"bottom={PAGE_BOTTOM_MARGIN_MM}mm]{{geometry}}\n"
        "\\usepackage{longdivision}\n"
        "\\usepackage{xlop}\n"
        "\\usepackage{array}\n"
        "\\usepackage[table]{xcolor}\n"
        "\\usepackage{fancyhdr}\n"
        "\\pagestyle{fancy}\n"
        "\\fancyhf{}\n"
        f"\\fancyfoot[L]{{{COPYRIGHT_STR}}}\n"
        "\\fancyfoot[R]{Page \\#\\thepage}\n"
        "\\renewcommand{\\headrulewidth}{0pt}\n"
        "\\renewcommand{\\footrulewidth}{0pt}\n"
        f"\\addtolength{{\\footskip}}{{{FOOTER_TEXT_LOWERING_MM}mm}}\n"
        "\\setlength{\\parindent}{0pt}\n"
    )


def build_page_header_tex() -> str:
    return (
        f"{{\\bfseries {HEADER_STR}}}\\\\\n"
        f"{{\\Large\\bfseries {TITLE_STR}}}\\\\\n"
        f"{{\\small {SUB_TITLE_STR}}}\\\\[1em]\n"
        "Date: \\underline{\\hspace{4cm}} \\hfill Time: \\underline{\\hspace{4cm}}\n"
        "\\vspace{1.5em}\n\n"
    )


def build_inline_grid_tex(blocks: list[str], columns: int) -> str:
    """Lay out horizontal problem rows across the full page body.

    Each visual row uses equal-width cells spanning ``\\textwidth``, keeping
    each problem centered in its allocated column regardless of the number
    of columns. ``\\vfill`` before every row lets TeX distribute the
    remaining printable height between the header, rows, optional bottom
    answer, and footer area.
    """
    column_width_tex = (
        f"\\dimexpr(\\textwidth-{TABCOLSEP_COUNT_PER_COLUMN * columns}\\tabcolsep)/{columns}\\relax"
    )
    column_spec = f">{{\\centering\\arraybackslash}}p{{{column_width_tex}}}" * columns
    row_tabulars = []
    for row_blocks in build_column_major_rows(blocks, columns):
        row_blocks += [''] * (columns - len(row_blocks))
        row_tex = ' & '.join(row_blocks)
        row_tabulars.append(
            "\\vfill\n"
            f"\\noindent\\begin{{tabular}}{{{column_spec}}}\n{row_tex}\\\\\n\\end{{tabular}}"
        )
    return '\n'.join(row_tabulars)


def build_column_major_rows(blocks: list[str], columns: int) -> list[list[str]]:
    """Convert sequential blocks to visual rows filled down each column first."""
    row_count = (len(blocks) + columns - 1) // columns
    return [
        [
            blocks[column * row_count + row]
            for column in range(columns)
            if column * row_count + row < len(blocks)
        ]
        for row in range(row_count)
    ]


def build_tabular_grid_tex(blocks: list[str], columns: int) -> str:
    """
    Arrange blocks into rows of a LaTeX tabular, one block per cell.

    Used for --vertical blocks (xlop/longdivision output), which are
    multi-row LaTeX content that would break \\hspace-based inline joining
    (build_inline_grid_tex); a tabular cell keeps each block's rows
    self-contained and column-aligned regardless of its neighbors' height.
    Column width is computed from \\textwidth so the grid adapts to the
    page's paper size and column count, with \\tabcolsep padding
    subtracted to avoid an overfull row.

    Each row is emitted as its own single-row tabular, joined by the same
    \\par\\vspace break build_inline_grid_tex uses between rows, rather
    than one tabular spanning every row: a plain `tabular` cannot break
    across a page boundary, so a tall multi-row grid (e.g. the default
    10 rows) would otherwise be pushed as one unbreakable block, leaving
    the current page blank and overflowing past the next page's bottom
    margin instead of just flowing onto it row by row.
    """
    column_width_tex = (
        f"\\dimexpr(\\textwidth-{TABCOLSEP_COUNT_PER_COLUMN * columns}\\tabcolsep)/{columns}\\relax"
    )
    column_spec = f">{{\\centering\\arraybackslash}}p{{{column_width_tex}}}" * columns
    row_tabulars = []
    for row_blocks in build_column_major_rows(blocks, columns):
        row_blocks += [''] * (columns - len(row_blocks))
        row_tex = ' & '.join(row_blocks)
        row_tabulars.append(f"\\begin{{tabular}}{{{column_spec}}}\n{row_tex}\n\\end{{tabular}}")
    return f"\\par\\vspace{{{ROW_VSPACE_EM}em}}\n".join(row_tabulars)


def build_block_grid_tex(blocks: list[str]) -> str:
    """Vertically center self-contained blocks without nesting LaTeX tables."""
    return "\\vfill\n" + "\n".join(blocks) + "\n\\vfill"


def build_page_tex(page: Page) -> str:
    """Render one Page's grid of blocks, plus header and optional bottom answer."""
    if page.layout == 'tabular':
        grid_tex = build_tabular_grid_tex(page.blocks, page.columns)
    elif page.layout == 'block':
        grid_tex = build_block_grid_tex(page.blocks)
    else:
        grid_tex = build_inline_grid_tex(page.blocks, page.columns)

    parts = [build_page_header_tex(), grid_tex]
    if page.bottom_answer_tex:
        parts.append(f"\\vfill\n{{\\small {page.bottom_answer_tex}}}\n")
    return "\n".join(parts)


def build_document_tex(paper_size: str, blank_pages: list[Page], filled_pages: list[Page], mode: str) -> str:
    """
    Build a full LaTeX document.

    Args:
        mode: 'blank' (practice sheet only), 'filled' (worked answer key
            only), or 'merge' (each blank page immediately followed by its
            filled counterpart, in one PDF -- a simplified variant of
            nuts_calc.py's `--merge`, which instead delays the answer page
            by one page; see module/L3 docs for details).
    """
    if mode == 'blank':
        ordered_pages = blank_pages
    elif mode == 'filled':
        ordered_pages = filled_pages
    else:
        ordered_pages = []
        for blank_page, filled_page in zip(blank_pages, filled_pages):
            ordered_pages.append(blank_page)
            ordered_pages.append(filled_page)

    document_body = "\n\\newpage\n".join(build_page_tex(page) for page in ordered_pages)
    return (
        build_preamble_tex(paper_size)
        + "\\begin{document}\n"
        + document_body
        + "\n\\end{document}\n"
    )


def compile_tex(tex_source: str, out_pdf_path: str) -> None:
    env = os.environ.copy()
    env['TEXINPUTS'] = f"{VENDOR_TEXMF_DIR}//:" + env.get('TEXINPUTS', '')
    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, 'worksheet.tex')
        with open(tex_path, 'w') as f:
            f.write(tex_source)
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'worksheet.tex'],
            cwd=tmp_dir, env=env, capture_output=True, text=True,
        )
        if result.returncode != 0:
            failure(f"pdflatex failed while building {out_pdf_path}:\n{result.stdout[-4000:]}")
        shutil.copyfile(os.path.join(tmp_dir, 'worksheet.pdf'), out_pdf_path)


def write_csv(rows: list[list[object]], csv_path: str) -> None:
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


@dataclass
class OpeProblem:
    """
    One generated `ope` (add/sub/mul/div) arithmetic problem.

    a/b/c always remain the raw (unscaled) integers `calc_add`/`calc_sub`/
    `calc_mul`/`calc_div` produce -- a_decimal_places/b_decimal_places (0 by
    default, meaning "plain integer") record where a decimal point should be
    displayed when rendering, via format_decimal_value/
    ope_result_decimal_places. This keeps all arithmetic in exact integers
    (never floats), so a decimal result is always exact and finite by
    construction -- see nuts_calc_tex.py.md's decimal-arithmetic design note.

    remainder (0 by default) is only meaningful for operator == 'div': `c` is
    always the floor quotient (a // b), and remainder is `a - b * c` (0 for
    an exact division). Every other operator leaves it at the default.
    """
    index: int
    a: int
    b: int
    operator: str
    c: int
    a_decimal_places: int = MIN_DECIMAL_PLACES
    b_decimal_places: int = MIN_DECIMAL_PLACES
    remainder: int = 0


def format_decimal_value(raw: int, places: int) -> str:
    """
    Format a raw scaled integer as a decimal string with `places` digits
    after the decimal point (places <= 0 returns the plain integer string,
    unchanged from pre-decimal-support behavior).
    """
    if places <= 0:
        return str(raw)
    digits = str(raw).zfill(places + 1)
    return f"{digits[:-places]}.{digits[-places:]}"


def ope_result_decimal_places(operator: str, a_places: int, b_places: int) -> int:
    """
    Decimal places of an `ope` result, derived from the operator and the
    operands' decimal places (which _init() guarantees are equal for
    add/sub/mix, and a_places >= b_places for div):
    - add/sub (and mix, which requires equal places): same as the operands.
    - mul: a_places + b_places (e.g. 3.6 x 2.4 -> 2 places).
    - div: a_places - b_places (aligning decimal points before dividing, as
      taught in the course of study -- e.g. 6.4 / 1.6 has 0 places, 6.4 / 2
      has 1). Always >= 0 (enforced by _init()), and exact because calc_div
      only accepts a raw a % b == 0.
    """
    if operator == 'mul':
        return a_places + b_places
    if operator == 'div':
        return a_places - b_places
    return a_places


def addition_has_carry(a: int, b: int) -> bool:
    """Whether adding two non-negative integers produces a carry in any digit."""
    a = abs(a)
    b = abs(b)
    while a > 0 or b > 0:
        if a % 10 + b % 10 >= 10:
            return True
        a //= 10
        b //= 10
    return False


def subtraction_has_borrow(a: int, b: int) -> bool:
    """Whether subtracting two non-negative integers borrows in any digit."""
    a = abs(a)
    b = abs(b)
    while a > 0 or b > 0:
        if a % 10 < b % 10:
            return True
        a //= 10
        b //= 10
    return False


def operand_digit_width(values: list[int]) -> int:
    """Return the widest decimal digit count represented by an operand range."""
    return max(1, max(len(str(abs(value))) for value in values))


def build_addition_fallback(carry: bool, a_width: int, b_width: int) -> tuple[int, int]:
    """Build positive operands of the requested widths that satisfy `carry`."""
    if carry:
        a = 1 if a_width == 1 else 10 ** (a_width - 1) + 1
        b = 9 if b_width == 1 else 10 ** (b_width - 1) + 9
        return a, b
    a = (10 ** a_width - 1) // 9
    b = (10 ** b_width - 1) // 9
    return a, b


def calc_add(
        a: int, b: int, nums_a: list[int], nums_b: list[int],
        carry: bool | None = None,
    ) -> tuple[int, int, int]:
    """
    Add two operands, optionally requiring or forbidding digit-wise carrying.

    A carry condition takes precedence over the configured operand bounds.
    Random samples prefer those bounds, but after the retry budget is
    exhausted a matching pair is synthesized with the same operand digit
    widths instead of failing. With carry=None, the original operands are
    returned immediately, preserving the pre-option behavior exactly.
    """
    if carry is None:
        return a, b, a + b
    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if addition_has_carry(a, b) is carry:
            return a, b, a + b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    a, b = build_addition_fallback(
        carry, operand_digit_width(nums_a), operand_digit_width(nums_b),
    )
    return a, b, a + b


def build_subtraction_fallback(a_width: int, b_width: int) -> tuple[int, int]:
    """Build positive, borrow-free operands while preserving widths where possible."""
    a_width = max(a_width, b_width)
    a = 8 * ((10 ** a_width - 1) // 9)
    b = (10 ** b_width - 1) // 9
    return a, b


def calc_sub(
        a: int, b: int, nums_a: list[int], nums_b: list[int],
        borrow: bool | None = None,
    ) -> tuple[int, int, int]:
    """
    Subtract with a positive result, optionally requiring/forbidding borrowing.

    borrow=True deliberately overrides configured ranges and restricts the
    problem to 10-19 minus a one-digit operand. borrow=False prefers the
    configured ranges, then synthesizes a positive borrow-free pair instead
    of failing. borrow=None preserves the original retry/fallback behavior.
    """
    if borrow is True:
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            a = random.choice(BORROWING_MINUENDS)
            b = random.choice(BORROWING_SUBTRAHENDS)
            if subtraction_has_borrow(a, b):
                return a, b, a - b
        return 10, 1, 9

    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if a - b > 0 and (borrow is None or not subtraction_has_borrow(a, b)):
            return a, b, a - b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    if borrow is False:
        a, b = build_subtraction_fallback(
            operand_digit_width(nums_a), operand_digit_width(nums_b),
        )
        return a, b, a - b
    a, b = max(nums_a), min(nums_b)
    if a - b > 0:
        return a, b, a - b
    raise ValueError(
        "No subtraction pair with a positive result (a - b > 0) "
        "found in the given number ranges."
    )


def calc_mul(a: int, b: int, nums_a: list[int], nums_b: list[int]) -> tuple[int, int, int]:
    return a, b, a * b


def find_exact_division_pair(nums_a: list[int], nums_b: list[int]) -> tuple[int, int] | None:
    """
    Deterministically find one (a, b) pair with b != 0 and a % b == 0.

    Used as calc_div's fallback when MAX_OPERAND_RETRY_ATTEMPTS of random
    sampling doesn't find a solution (possible when the valid-pair space
    is a small fraction of nums_a x nums_b). For each candidate divisor,
    only its multiples within the nums_a range are probed (not every
    nums_a element), so this stays cheap even for large ranges.
    """
    if not nums_a:
        return None
    nums_a_set = set(nums_a)
    a_min, a_max = min(nums_a_set), max(nums_a_set)
    for b in nums_b:
        if b == 0:
            continue
        first_multiple = -(-a_min // b) * b  # ceiling division
        for candidate in range(first_multiple, a_max + 1, abs(b)):
            if candidate in nums_a_set:
                return candidate, b
    return None


def find_remainder_division_pair(nums_a: list[int], nums_b: list[int]) -> tuple[int, int] | None:
    """
    Deterministically find one (a, b) pair with b != 0 and a % b != 0.

    Used as calc_div's fallback (remainder=True) when MAX_OPERAND_RETRY_ATTEMPTS
    of random sampling doesn't find a solution. Mirrors find_exact_division_pair's
    role for the remainder=False path, but a non-multiple is common enough that a
    plain scan (rather than find_exact_division_pair's multiples-only stepping,
    which only makes sense for *exact* multiples) stays cheap in practice.
    """
    for b in nums_b:
        if b == 0:
            continue
        for a in nums_a:
            if a % b != 0:
                return a, b
    return None


def calc_div(
        a: int, b: int, nums_a: list[int], nums_b: list[int],
        remainder: bool | None = None,
    ) -> tuple[int, int, int]:
    """
    Retry with freshly-sampled operands until the division matches `remainder`.

    remainder=None/False retries until the division is exact (a % b == 0),
    falling back to find_exact_division_pair if random sampling exhausts
    MAX_OPERAND_RETRY_ATTEMPTS without success -- this is the pre-remainder-
    support behavior, unchanged. remainder=True retries until the division
    has a nonzero remainder (a % b != 0), falling back to
    find_remainder_division_pair. The returned `c` is always the floor
    quotient (a // b); the caller (generate_ope_problems) derives the
    remainder itself as `a - b * c` for display.
    """
    if remainder:
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            if b != 0 and a % b != 0:
                return a, b, a // b
            a = random.choice(nums_a)
            b = random.choice(nums_b)
        fallback = find_remainder_division_pair(nums_a, nums_b)
        if fallback is not None:
            a, b = fallback
            return a, b, a // b
        raise ValueError(
            "No remainder pair (a % b != 0, b != 0) found in the given number ranges."
        )

    for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
        if b != 0 and a % b == 0:
            return a, b, a // b
        a = random.choice(nums_a)
        b = random.choice(nums_b)
    fallback = find_exact_division_pair(nums_a, nums_b)
    if fallback is not None:
        a, b = fallback
        return a, b, a // b
    raise ValueError(
        "No exact-division pair (a % b == 0, b != 0) found in the given number ranges."
    )


CALC_FUNCTIONS: dict[str, Callable[[int, int, list[int], list[int]], tuple[int, int, int]]] = {
    'add': calc_add,
    'sub': calc_sub,
    'mul': calc_mul,
    'div': calc_div,
}


def generate_ope_problems(
        nums_a: list[int], nums_b: list[int], operators: list[str],
        order: int, start_index: int,
        a_decimal_places: int = MIN_DECIMAL_PLACES, b_decimal_places: int = MIN_DECIMAL_PLACES,
        carry_mode: CarryMode | None = None,
        remainder_mode: RemainderMode | None = None,
    ) -> list[OpeProblem]:
    """
    Generate `order` arithmetic problems starting at `start_index`.

    `operators=['mix']` picks a random operator (add/sub/mul/div) per
    problem; otherwise one operator is picked per problem from `operators`.

    carry_mode='required' requires carrying for add and borrowing for sub;
    'none' forbids both. 'mixed' leaves one-digit addition unrestricted and
    chooses borrow-free one-digit or borrowing 10-19-minus-one-digit
    subtraction per subtraction problem.

    remainder_mode='required' requires a nonzero division remainder;
    'none' forbids one (same as the pre-remainder-support default);
    'mixed' chooses per div problem. OpeProblem.remainder is derived from
    the returned a/b/c as `a - b * c` regardless of remainder_mode, so it's
    always populated correctly (0 for an exact division).

    a_decimal_places/b_decimal_places (0 by default) do not change how
    nums_a/nums_b/CALC_FUNCTIONS are sampled or validated -- they are only
    recorded on the resulting OpeProblem for display (see
    ope_result_decimal_places/format_decimal_value). _init() guarantees the
    operand/operator combination keeps every result an exact, finite value.
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        a = random.choice(nums_a)
        b = random.choice(nums_b)
        operator = random.choice(effective_operators)
        if operator == 'add':
            carry = None if carry_mode in (None, 'mixed') else carry_mode == 'required'
            a, b, c = calc_add(a, b, nums_a, nums_b, carry)
        elif operator == 'sub' and carry_mode is not None:
            borrow = random.choice((False, True)) if carry_mode == 'mixed' else carry_mode == 'required'
            a, b, c = calc_sub(a, b, nums_a, nums_b, borrow)
        elif operator == 'div' and remainder_mode is not None:
            want_remainder = random.choice((False, True)) if remainder_mode == 'mixed' else remainder_mode == 'required'
            a, b, c = calc_div(a, b, nums_a, nums_b, want_remainder)
        else:
            a, b, c = CALC_FUNCTIONS[operator](a, b, nums_a, nums_b)
        remainder = a - b * c if operator == 'div' else 0
        problems.append(OpeProblem(
            index=start_index + offset, a=a, b=b, operator=operator, c=c,
            a_decimal_places=a_decimal_places, b_decimal_places=b_decimal_places,
            remainder=remainder,
        ))
    return problems


def build_horizontal_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """
    Render one `ope` problem in horizontal format: `n) $a op b = c$`.

    A div problem with a nonzero remainder additionally renders a
    "\\cdots r" suffix (blanked out along with `c` when show_answer=False),
    since `c = a // b` alone would otherwise understate the answer. Uses the
    plain-math "3 \\cdots 2" ellipsis shorthand (also used in Japanese
    textbooks) for the remainder marker rather than the word "あまり":
    this file compiles with plain pdflatex (no CJK/Japanese font package),
    which cannot render Japanese text (see docs/L3_implementation/
    nuts_calc_tex.py.md).
    """
    symbol = OPERATOR_TEX_SYMBOLS[problem.operator]
    a_tex = format_decimal_value(problem.a, problem.a_decimal_places)
    b_tex = format_decimal_value(problem.b, problem.b_decimal_places)
    if show_answer:
        c_places = ope_result_decimal_places(problem.operator, problem.a_decimal_places, problem.b_decimal_places)
        result_tex = format_decimal_value(problem.c, c_places)
        remainder_tex = f" \\cdots {problem.remainder}" if problem.remainder else ""
    else:
        result_tex = BLANK_ANSWER_TEX
        remainder_tex = f" \\cdots {BLANK_ANSWER_TEX}" if problem.remainder else ""
    return f"{problem.index}) ${a_tex} {symbol} {b_tex} = {result_tex}{remainder_tex}$"


def build_intermediate_memo(a: int, b: int) -> str:
    """
    2-digit x 1-digit mental-math memo technique (see memo.md STEP 1):
    concatenate (tens digit of a) x b and (ones digit of a) x b, each
    zero-padded to 2 digits.
    """
    tens_digit, ones_digit = divmod(a, 10)
    return f"{tens_digit * b:02d}{ones_digit * b:02d}"


def build_horizontal_intermediate_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """Render one `ope --intermediate` problem: `n) $a * b => memo => c$`."""
    memo = build_intermediate_memo(problem.a, problem.b)
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.a} \\times {problem.b} \\Rightarrow {memo} \\Rightarrow {result_tex}$"


def build_vertical_block_tex(problem: OpeProblem, show_answer: bool) -> str:
    """
    Render one `ope --vertical` (hissan) problem as a tabular-cell block:
    index label, then the LaTeX-rendered written-calculation layout.

    add/sub/mul use the `xlop` package (auto-rendering carries and, for a
    multi-digit multiplier, one partial-product row per digit). div uses
    `longdivision`. For the blank (practice) variant, xlop's per-digit
    style hooks (resultstyle/carrystyle/intermediarystyle) are overridden
    to `\\phantom`, which reserves the digits' layout space without
    printing them; longdivision has an equivalent built-in via its
    `stage=0` option (only the bracket/divisor/dividend are shown).
    """
    index_line = f"{problem.index})\\newline "
    if problem.operator == 'div':
        stage_option = '' if show_answer else '[stage=0]'
        return f"{index_line}\\[\\intlongdivision{stage_option}{{{problem.a}}}{{{problem.b}}}\\]"

    command = XLOP_VERTICAL_COMMANDS[problem.operator]
    op_call_tex = f"\\[\\{command}{{{problem.a}}}{{{problem.b}}}\\]"
    if show_answer:
        return (
            index_line
            + f"\\begingroup\\opset{{{XLOP_VERTICAL_LAYOUT_OPTIONS}}}"
            + op_call_tex
            + "\\endgroup"
        )
    return (
        index_line
        + "\\begingroup\\opset{"
        + XLOP_VERTICAL_LAYOUT_OPTIONS
        + ",resultstyle=\\phantom,carrystyle=\\phantom,intermediarystyle=\\phantom}"
        + op_call_tex
        + "\\endgroup"
    )


def build_ope_page_pair(problems: list[OpeProblem], columns: int, vertical: bool, intermediate: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `ope` problems."""
    if vertical:
        block_builder: Callable[[OpeProblem, bool], str] = build_vertical_block_tex
        layout = 'tabular'
    elif intermediate:
        block_builder = build_horizontal_intermediate_block_tex
        layout = 'inline'
    else:
        block_builder = build_horizontal_block_tex
        layout = 'inline'

    blank_page = Page(
        blocks=[block_builder(problem, show_answer=False) for problem in problems],
        columns=columns, layout=layout,
    )
    filled_page = Page(
        blocks=[block_builder(problem, show_answer=True) for problem in problems],
        columns=columns, layout=layout,
    )
    return blank_page, filled_page


def build_ope_bottom_answer_tex(problems: list[OpeProblem]) -> str:
    parts = []
    for problem in problems:
        c_places = ope_result_decimal_places(problem.operator, problem.a_decimal_places, problem.b_decimal_places)
        answer = format_decimal_value(problem.c, c_places)
        if problem.remainder:
            # See build_horizontal_block_tex's docstring for why this uses
            # "..." rather than "あまり" (plain pdflatex, no CJK support).
            answer += f" ... {problem.remainder}"
        parts.append(f"({problem.index}) {answer}")
    return ' \\quad '.join(parts)


def build_ope_csv_rows(pages_problems: list[list[OpeProblem]]) -> list[list[object]]:
    """
    One row per problem: [page_number, index, a, operator, b, c, remainder].

    a/b/c stay plain int when a_decimal_places/b_decimal_places are both 0
    (the pre-decimal-support default); with decimal places, they are
    formatted decimal strings. remainder is always a plain int (0 for every
    non-div problem and every exact division), appended as a trailing
    column so pre-remainder-support CSV consumers that only read the first
    six columns are unaffected.
    """
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            if problem.a_decimal_places == MIN_DECIMAL_PLACES and problem.b_decimal_places == MIN_DECIMAL_PLACES:
                a_value: object = problem.a
                b_value: object = problem.b
                c_value: object = problem.c
            else:
                c_places = ope_result_decimal_places(problem.operator, problem.a_decimal_places, problem.b_decimal_places)
                a_value = format_decimal_value(problem.a, problem.a_decimal_places)
                b_value = format_decimal_value(problem.b, problem.b_decimal_places)
                c_value = format_decimal_value(problem.c, c_places)
            rows.append([page_number, problem.index, a_value, problem.operator, b_value, c_value, problem.remainder])
    return rows


@dataclass
class MultiTermOpeProblem:
    """
    One flat (non-parenthesized) `ope` problem with 2+ terms, generalizing
    OpeProblem. `len(operators) == len(operands) - 1`.

    When `mixed` is False, every entry in `operators` is identical (today's
    per-problem single-operator behavior generalized to N terms, evaluated
    strictly left-to-right via evaluate_left_to_right). When `mixed` is
    True, operators may differ per gap and the expression is evaluated with
    standard operator precedence (* / before + -), not left-to-right -- see
    evaluate_mixed_expression().
    """
    index: int
    operands: list[int]
    operators: list[str]
    mixed: bool
    result: int


@dataclass
class ExprTreeNode:
    """
    One node of a binary expression tree used by `ope --use-parentheses`.

    Leaves have `left = right = None` and hold an operand in `value`;
    internal nodes have an `operator` and two children, with `value` filled
    in as that subtree's evaluated result once evaluate_expr_tree() succeeds
    for it.
    """
    value: int = 0
    operator: str | None = None
    left: 'ExprTreeNode | None' = None
    right: 'ExprTreeNode | None' = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None


@dataclass
class TreeOpeProblem:
    """
    One `ope --use-parentheses` problem: a random binary expression tree
    over N>=3 operands, rendered with parentheses around every internal
    node except the root (see render_expr_tree). Generalizes the former
    fixed-3-operand a/b/c/op_left/op_right/position shape -- N=3 is simply
    the tree with 3 leaves, not a distinct code path.

    `operands`/`operators` are flattened convenience views (leaves
    left-to-right, internal-node operators pre-order, via flatten_tree) --
    they do not by themselves encode the tree shape, only `tree` does.
    """
    index: int
    operands: list[int]
    operators: list[str]
    tree: ExprTreeNode
    result: int


def paren_stage_add(x: int, y: int) -> int | None:
    return x + y


def paren_stage_sub(x: int, y: int) -> int | None:
    return x - y if x - y > 0 else None


def paren_stage_mul(x: int, y: int) -> int | None:
    return x * y


def paren_stage_div(x: int, y: int) -> int | None:
    return x // y if y != 0 and x % y == 0 else None


# Shared per-step validity check (positive subtraction result, exact
# division) reused by ope --use-parentheses's tree evaluation
# (evaluate_expr_tree) and plain multi-term ope's chained/grouped
# evaluation (evaluate_left_to_right) -- not parentheses-specific despite
# the name, kept for backward compatibility with existing tests/CSV data.
PAREN_STAGE_FUNCTIONS: dict[str, Callable[[int, int], int | None]] = {
    'add': paren_stage_add,
    'sub': paren_stage_sub,
    'mul': paren_stage_mul,
    'div': paren_stage_div,
}


def mixed_stage_add(x: Fraction, y: Fraction) -> Fraction | None:
    return x + y


def mixed_stage_sub(x: Fraction, y: Fraction) -> Fraction | None:
    result = x - y
    return result if result > 0 else None


def mixed_stage_mul(x: Fraction, y: Fraction) -> Fraction | None:
    return x * y


def mixed_stage_div(x: Fraction, y: Fraction) -> Fraction | None:
    # y is always > 0 (every MixedOperand kind generates a positive value),
    # and Fraction division is always exact -- no repeating/infinite-decimal
    # risk, since the "mixed" command renders answers as fractions, never
    # decimal notation (see build_mixed_block_tex).
    return x / y


# Fraction counterpart of PAREN_STAGE_FUNCTIONS, used by the "mixed" command
# (int/decimal/fraction operands, all resolved to exact Fraction values) via
# evaluate_left_to_right/evaluate_mixed_expression's stage_functions param.
MIXED_STAGE_FUNCTIONS: dict[str, Callable[[Fraction, Fraction], Fraction | None]] = {
    'add': mixed_stage_add,
    'sub': mixed_stage_sub,
    'mul': mixed_stage_mul,
    'div': mixed_stage_div,
}


def build_tree_shape(leaf_count: int) -> ExprTreeNode:
    """
    Build a random binary tree shape with `leaf_count` leaves (values/
    operators left as placeholders; see assign_tree_operands/
    assign_tree_operators).

    Recursively picks a random split point in [1, leaf_count-1] and
    partitions the leaves into a left subtree of that size and a right
    subtree of the remainder. This is one standard, simple, correct way to
    generate a random binary tree shape (not the only one -- e.g.
    uniform-over-Catalan-shapes sampling is an alternative with a flatter
    shape distribution). For leaf_count == 3, the only two possible splits
    (1/2 and 2/1) exactly reproduce the two shapes the former fixed-3-term
    implementation produced (position='right'/'left' respectively), each
    equally likely.
    """
    if leaf_count == 1:
        return ExprTreeNode()
    split = random.randint(1, leaf_count - 1)
    return ExprTreeNode(left=build_tree_shape(split), right=build_tree_shape(leaf_count - split))


def collect_leaves(node: ExprTreeNode) -> list[ExprTreeNode]:
    """Collect a tree's leaf nodes in left-to-right (in-order) order."""
    if node.is_leaf:
        return [node]
    return collect_leaves(node.left) + collect_leaves(node.right)


def assign_tree_operands(root: ExprTreeNode, nums_a: list[int], nums_b: list[int]) -> None:
    """
    Assign a value to each leaf of `root`, in place.

    The leftmost leaf draws from `nums_a`; every other leaf draws from
    `nums_b` -- generalizing --use-parentheses's former `nums_c = nums_b`
    convention (the 3rd operand reusing the -b/--b-value range) to
    arbitrary N (see docs/L3_implementation/nuts_calc_tex.py.md).
    """
    leaves = collect_leaves(root)
    for index, leaf in enumerate(leaves):
        leaf.value = random.choice(nums_a) if index == 0 else random.choice(nums_b)


def assign_tree_operators(
        node: ExprTreeNode, effective_operators: list[str], mixed: bool, shared_operator: str | None,
    ) -> None:
    """
    Assign an operator to each internal node of `node`, in place.

    One operator for the whole tree when `mixed` is False (`shared_operator`,
    chosen once by the caller); an independently-drawn operator per internal
    node when `mixed` is True.
    """
    if node.is_leaf:
        return
    node.operator = random.choice(effective_operators) if mixed else shared_operator
    assign_tree_operators(node.left, effective_operators, mixed, shared_operator)
    assign_tree_operators(node.right, effective_operators, mixed, shared_operator)


def evaluate_expr_tree(node: ExprTreeNode) -> int | None:
    """
    Evaluate `node` bottom-up (post-order), reusing PAREN_STAGE_FUNCTIONS's
    per-node validity check (positive subtraction, exact division).

    Returns None as soon as any subtree is invalid, propagated up for the
    caller to redraw and retry the whole tree (shape + operators +
    operands) -- generalizing generate_paren_ope_problems's former
    no-deterministic-fallback convention.
    """
    if node.is_leaf:
        return node.value
    left = evaluate_expr_tree(node.left)
    if left is None:
        return None
    right = evaluate_expr_tree(node.right)
    if right is None:
        return None
    result = PAREN_STAGE_FUNCTIONS[node.operator](left, right)
    if result is not None:
        node.value = result
    return result


def flatten_tree(node: ExprTreeNode) -> tuple[list[int], list[str]]:
    """
    Flatten a tree into (leaves left-to-right, internal-node operators
    pre-order). Convenience-only view for TreeOpeProblem.operands/
    operators; does not by itself encode the tree shape (`tree` does).
    """
    if node.is_leaf:
        return [node.value], []
    left_operands, left_operators = flatten_tree(node.left)
    right_operands, right_operators = flatten_tree(node.right)
    return left_operands + right_operands, [node.operator] + left_operators + right_operators


def generate_tree_ope_problems(
        nums_a: list[int], nums_b: list[int], operators: list[str], mixed: bool,
        terms_min: int, terms_max: int, order: int, start_index: int,
    ) -> list[TreeOpeProblem]:
    """
    Generate `order` parenthesized N-term problems starting at `start_index`,
    each problem independently drawing its term count from
    [terms_min, terms_max].

    For each problem, the tree shape, every node's operator, and every
    leaf's value are redrawn together on each retry (bounded by
    MAX_OPERAND_RETRY_ATTEMPTS) until evaluate_expr_tree succeeds --
    simpler than (and a behavior change from) the former
    generate_paren_ope_problems, which fixed op_left/op_right/position once
    and only redrew a/b/c. Like that function, there is no deterministic
    fallback: an exhausted retry budget raises ValueError. Larger/deeper
    trees have strictly more nodes that can each independently fail
    validity, so the odds of exhausting the budget are worse than the
    former fixed-3-term case.
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        leaf_count = random.randint(terms_min, terms_max)
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            shared_operator = None if mixed else random.choice(effective_operators)
            tree = build_tree_shape(leaf_count)
            assign_tree_operands(tree, nums_a, nums_b)
            assign_tree_operators(tree, effective_operators, mixed, shared_operator)
            result = evaluate_expr_tree(tree)
            if result is not None:
                operands, tree_operators = flatten_tree(tree)
                problems.append(TreeOpeProblem(
                    index=start_index + offset, operands=operands,
                    operators=tree_operators, tree=tree, result=result,
                ))
                break
        else:
            raise ValueError(
                f"No valid {leaf_count}-term expression tree found within the given number ranges."
            )
    return problems


def render_expr_tree(node: ExprTreeNode, symbol_for_operator: Callable[[str], str], is_root: bool = True) -> str:
    """
    Recursively render `node`, wrapping every internal node except the root
    in parentheses.

    Reproduces the former fixed-3-term renderer exactly for N=3: for
    position='left' (`(a op_left b) op_right c`), the tree is
    root=op_right(internal(op_left, a, b), leaf c); rendering the left
    child (not root) yields "(a op_left b)", giving
    "(a op_left b) op_right c" overall. position='right' is symmetric.
    """
    if node.is_leaf:
        return str(node.value)
    inner = (
        f"{render_expr_tree(node.left, symbol_for_operator, False)} "
        f"{symbol_for_operator(node.operator)} "
        f"{render_expr_tree(node.right, symbol_for_operator, False)}"
    )
    return inner if is_root else f"({inner})"


def build_tree_ope_expression_tex(tree: ExprTreeNode) -> str:
    return render_expr_tree(tree, lambda operator: OPERATOR_TEX_SYMBOLS[operator])


def build_tree_ope_structure_text(tree: ExprTreeNode) -> str:
    """Render-agnostic structure string for CSV output, e.g. "(5 add 3) mul 2"."""
    return render_expr_tree(tree, lambda operator: operator)


def build_tree_ope_block_tex(problem: TreeOpeProblem, show_answer: bool) -> str:
    """Render one `ope --use-parentheses` problem: `n) $<expression> = result$`."""
    result_tex = str(problem.result) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${build_tree_ope_expression_tex(problem.tree)} = {result_tex}$"


def build_tree_ope_page_pair(problems: list[TreeOpeProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of parenthesized `ope` problems."""
    blank_page = Page(
        blocks=[build_tree_ope_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns, layout='inline',
    )
    filled_page = Page(
        blocks=[build_tree_ope_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns, layout='inline',
    )
    return blank_page, filled_page


def build_tree_ope_bottom_answer_tex(problems: list[TreeOpeProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.result}" for problem in problems)


def build_tree_ope_csv_rows(pages_problems: list[list[TreeOpeProblem]]) -> list[list[object]]:
    """
    One row per problem: [page_number, index, terms, structure, result].

    `structure` is a single self-describing string (e.g. "(5 add 3) mul 2")
    encoding nesting, values, and operators together, replacing the former
    fixed 10-column [a, op_left, b, op_right, c, position, inner] shape
    which cannot scale to a variable number of operands.
    """
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index, len(problem.operands),
                build_tree_ope_structure_text(problem.tree), problem.result,
            ])
    return rows


def build_tree_ope_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[TreeOpeProblem]]]:
    """Generate real `ope --use-parentheses` problems and their blank/filled Page pairs for every page."""
    nums_a = list(range(ini.a_min, ini.a_max + 1))
    nums_b = list(range(ini.b_min, ini.b_max + 1))
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_tree_ope_problems(
            nums_a, nums_b, ini.operator, ini.mixed_operators,
            ini.terms_min, ini.terms_max, order, start_index,
        )
        blank_page, filled_page = build_tree_ope_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_tree_ope_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


StageValue = TypeVar('StageValue')


def evaluate_left_to_right(
        operands: list[StageValue], operators: list[str],
        stage_functions: dict[str, Callable[[StageValue, StageValue], StageValue | None]] = PAREN_STAGE_FUNCTIONS,
    ) -> StageValue | None:
    """
    Fold `operands`/`operators` strictly left-to-right, applying
    `stage_functions`'s per-step validity check at every step (e.g. for
    "a sub b sub c", both "a - b" and "(a - b) - c" must independently stay
    positive, not just the final result) -- generalizes calc_sub/calc_div's
    single-step check to an arbitrary-length chain. Returns None as soon as
    any step is invalid.

    `stage_functions` defaults to PAREN_STAGE_FUNCTIONS (plain-int `ope`
    problems); the "mixed" command passes MIXED_STAGE_FUNCTIONS instead to
    evaluate exact Fraction values.
    """
    accumulator = operands[0]
    for operand, operator in zip(operands[1:], operators):
        accumulator = stage_functions[operator](accumulator, operand)
        if accumulator is None:
            return None
    return accumulator


def split_into_precedence_groups(
        operands: list[StageValue], operators: list[str],
    ) -> tuple[list[list[StageValue]], list[list[str]], list[str]]:
    """
    Split a flat operand/operator sequence into standard-precedence groups:
    consecutive 'mul'/'div' operators extend the current group, 'add'/'sub'
    operators start a new group and are collected as connecting operators
    between groups. Returns (groups, per-group operators, connecting
    operators) for evaluate_mixed_expression to fold in two passes.

    Operand-value-agnostic (only inspects operator names), so it is shared
    unchanged by both plain-int `ope` and Fraction-valued "mixed" problems.
    """
    groups: list[list[StageValue]] = [[operands[0]]]
    group_operators: list[list[str]] = [[]]
    connecting_operators: list[str] = []
    for operand, operator in zip(operands[1:], operators):
        if operator in ('mul', 'div'):
            groups[-1].append(operand)
            group_operators[-1].append(operator)
        else:
            connecting_operators.append(operator)
            groups.append([operand])
            group_operators.append([])
    return groups, group_operators, connecting_operators


def evaluate_mixed_expression(
        operands: list[StageValue], operators: list[str],
        stage_functions: dict[str, Callable[[StageValue, StageValue], StageValue | None]] = PAREN_STAGE_FUNCTIONS,
    ) -> StageValue | None:
    """
    Evaluate a flat expression with standard operator precedence (* / bind
    tighter than + -, left-to-right within the same tier), without building
    an explicit tree: group consecutive mul/div operators via
    split_into_precedence_groups, evaluate each group with
    evaluate_left_to_right, then fold the group results together with
    evaluate_left_to_right again. Returns None if any group or the final
    fold is invalid. `stage_functions` is forwarded to both folding passes
    (see evaluate_left_to_right).
    """
    groups, group_operators, connecting_operators = split_into_precedence_groups(operands, operators)
    group_results = []
    for group_operands, operators_in_group in zip(groups, group_operators):
        group_result = evaluate_left_to_right(group_operands, operators_in_group, stage_functions)
        if group_result is None:
            return None
        group_results.append(group_result)
    return evaluate_left_to_right(group_results, connecting_operators, stage_functions)


def generate_multi_term_ope_problems(
        nums_a: list[int], nums_b: list[int], operators: list[str], mixed: bool,
        terms_min: int, terms_max: int, order: int, start_index: int,
    ) -> list[MultiTermOpeProblem]:
    """
    Generate `order` flat (non-parenthesized) N-term problems starting at
    `start_index`, each problem independently drawing its term count from
    [terms_min, terms_max].

    When `mixed` is False, one operator is chosen per problem and applied
    to every gap (evaluated via evaluate_left_to_right); when True, each gap
    gets an independently chosen operator (evaluated via
    evaluate_mixed_expression, standard precedence). All operands and
    operators are redrawn together on each retry (bounded by
    MAX_OPERAND_RETRY_ATTEMPTS); an exhausted budget raises ValueError, with
    no deterministic fallback (same convention as generate_tree_ope_problems).
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        term_count = random.randint(terms_min, terms_max)
        gap_count = term_count - 1
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            operands = [random.choice(nums_a)] + [random.choice(nums_b) for _ in range(gap_count)]
            if mixed:
                problem_operators = [random.choice(effective_operators) for _ in range(gap_count)]
                result = evaluate_mixed_expression(operands, problem_operators)
            else:
                shared_operator = random.choice(effective_operators)
                problem_operators = [shared_operator] * gap_count
                result = evaluate_left_to_right(operands, problem_operators)
            if result is not None:
                problems.append(MultiTermOpeProblem(
                    index=start_index + offset, operands=operands,
                    operators=problem_operators, mixed=mixed, result=result,
                ))
                break
        else:
            raise ValueError(
                f"No valid {term_count}-term expression found within the given number ranges (mixed={mixed})."
            )
    return problems


def build_multi_term_ope_expression_text(problem: MultiTermOpeProblem) -> str:
    """Render-agnostic expression string for CSV output, e.g. "5 sub 3 mul 2"."""
    parts = [str(problem.operands[0])]
    for operand, operator in zip(problem.operands[1:], problem.operators):
        parts += [operator, str(operand)]
    return ' '.join(parts)


def build_multi_term_ope_block_tex(problem: MultiTermOpeProblem, show_answer: bool) -> str:
    """Render one flat multi-term `ope` problem: `n) $a op1 b op2 c ... = result$` (no parentheses)."""
    parts = [str(problem.operands[0])]
    for operand, operator in zip(problem.operands[1:], problem.operators):
        parts += [OPERATOR_TEX_SYMBOLS[operator], str(operand)]
    result_tex = str(problem.result) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${' '.join(parts)} = {result_tex}$"


def build_multi_term_ope_page_pair(problems: list[MultiTermOpeProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of flat multi-term `ope` problems."""
    blank_page = Page(
        blocks=[build_multi_term_ope_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns, layout='inline',
    )
    filled_page = Page(
        blocks=[build_multi_term_ope_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns, layout='inline',
    )
    return blank_page, filled_page


def build_multi_term_ope_bottom_answer_tex(problems: list[MultiTermOpeProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.result}" for problem in problems)


def build_multi_term_ope_csv_rows(pages_problems: list[list[MultiTermOpeProblem]]) -> list[list[object]]:
    """One row per problem: [page_number, index, terms, mixed, expression, result]."""
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index, len(problem.operands), problem.mixed,
                build_multi_term_ope_expression_text(problem), problem.result,
            ])
    return rows


def build_multi_term_ope_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[MultiTermOpeProblem]]]:
    """Generate real flat multi-term `ope` problems and their blank/filled Page pairs for every page."""
    nums_a = list(range(ini.a_min, ini.a_max + 1))
    nums_b = list(range(ini.b_min, ini.b_max + 1))
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_multi_term_ope_problems(
            nums_a, nums_b, ini.operator, ini.mixed_operators,
            ini.terms_min, ini.terms_max, order, start_index,
        )
        blank_page, filled_page = build_multi_term_ope_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_multi_term_ope_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class MissingValueProblem:
    """
    One `ope --missing-value` problem: a op b = c with one of a/b boxed out.

    `blank` records which operand is hidden in the blank (practice) variant;
    the filled (answer) variant always shows all three values. `c` (the
    result) is never blanked: hiding it would be indistinguishable from
    plain `ope`'s default output (which already always hides the answer),
    not a genuine missing-number (mushikuizan) puzzle -- see
    MISSING_VALUE_POSITIONS.
    """
    index: int
    a: int
    b: int
    operator: str
    c: int
    blank: str  # 'a' | 'b'


# 'c' (the result) is deliberately excluded: blanking it produces the same
# shape as plain `ope`'s always-hide-the-answer output, not a real
# missing-number problem. Only the operand positions (a/b) are genuine
# missing-number blanks.
MISSING_VALUE_POSITIONS = ('a', 'b')


def generate_missing_value_problems(
        nums_a: list[int], nums_b: list[int], operators: list[str],
        order: int, start_index: int
    ) -> list[MissingValueProblem]:
    """
    Generate `order` missing-value problems starting at `start_index`.

    Reuses generate_ope_problems's operand/operator generation semantics
    directly (via CALC_FUNCTIONS) -- no new arithmetic logic is needed, since
    calc_sub/calc_div's existing validity checks (positive result / exact
    division) already guarantee a op b == c holds. Once that equation holds,
    hiding either operand is always solvable (e.g. "8 / __ = 4" is valid
    whenever "8 / 2 = 4" was), so no retry/fallback logic is required here.
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        a = random.choice(nums_a)
        b = random.choice(nums_b)
        operator = random.choice(effective_operators)
        a, b, c = CALC_FUNCTIONS[operator](a, b, nums_a, nums_b)
        blank = random.choice(MISSING_VALUE_POSITIONS)
        problems.append(MissingValueProblem(
            index=start_index + offset, a=a, b=b, operator=operator, c=c, blank=blank,
        ))
    return problems


def build_missing_value_block_tex(problem: MissingValueProblem, show_answer: bool) -> str:
    """Render one `ope --missing-value` problem: `n) $a op b = c$` with the blanked operand boxed. `c` is always shown."""
    symbol = OPERATOR_TEX_SYMBOLS[problem.operator]
    a_tex = str(problem.a) if show_answer or problem.blank != 'a' else BOXED_BLANK_TEX
    b_tex = str(problem.b) if show_answer or problem.blank != 'b' else BOXED_BLANK_TEX
    return f"{problem.index}) ${a_tex} {symbol} {b_tex} = {problem.c}$"


def build_missing_value_page_pair(problems: list[MissingValueProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of missing-value `ope` problems."""
    blank_page = Page(
        blocks=[build_missing_value_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns, layout='inline',
    )
    filled_page = Page(
        blocks=[build_missing_value_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns, layout='inline',
    )
    return blank_page, filled_page


MISSING_VALUE_TEX_VALUES: dict[str, Callable[[MissingValueProblem], int]] = {
    'a': lambda problem: problem.a,
    'b': lambda problem: problem.b,
}


def build_missing_value_bottom_answer_tex(problems: list[MissingValueProblem]) -> str:
    return ' \\quad '.join(
        f"({problem.index}) {MISSING_VALUE_TEX_VALUES[problem.blank](problem)}" for problem in problems
    )


def build_missing_value_csv_rows(pages_problems: list[list[MissingValueProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index, problem.a, problem.operator,
                problem.b, problem.c, problem.blank,
            ])
    return rows


def build_missing_value_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[MissingValueProblem]]]:
    """Generate real `ope --missing-value` problems and their blank/filled Page pairs for every page."""
    nums_a = list(range(ini.a_min, ini.a_max + 1))
    nums_b = list(range(ini.b_min, ini.b_max + 1))
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_missing_value_problems(nums_a, nums_b, ini.operator, order, start_index)
        blank_page, filled_page = build_missing_value_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_missing_value_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class ComProblem:
    """One generated `com` (complement-to-target) problem: a + c = target."""
    index: int
    a: int
    target: int
    c: int


def generate_com_problems(target: int, order: int, start_index: int) -> list[ComProblem]:
    """
    Generate `order` complement problems starting at `start_index`.

    `a` is drawn from 1..target-1 (inclusive) so the complement `c = target
    - a` is always a positive integer strictly less than `target`.
    """
    seed = list(range(1, target))
    problems = []
    for offset in range(order):
        a = random.choice(seed)
        problems.append(ComProblem(index=start_index + offset, a=a, target=target, c=target - a))
    return problems


def build_com_block_tex(problem: ComProblem, show_answer: bool) -> str:
    """Render one `com` problem with a boxed missing operand in the blank version."""
    result_tex = str(problem.c) if show_answer else BOXED_BLANK_TEX
    return f"{problem.index}) ${problem.a} + {result_tex} = {problem.target}$"


def build_com_page_pair(problems: list[ComProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `com` problems."""
    blank_page = Page(
        blocks=[build_com_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_com_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_com_bottom_answer_tex(problems: list[ComProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_com_csv_rows(pages_problems: list[list[ComProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.target, problem.c])
    return rows


def build_com_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[ComProblem]]]:
    """Generate real `com` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_com_problems(ini.a_value, order, start_index)
        blank_page, filled_page = build_com_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_com_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class HundredSquareTable:
    """One generated `100` addition table: left_values[r] + top_values[c] = the (r, c) cell."""
    left_values: list[int]
    top_values: list[int]

    @property
    def answers(self) -> list[list[int]]:
        return [[left + top for top in self.top_values] for left in self.left_values]


def sample_hundred_square_values(nums: list[int]) -> list[int]:
    """
    Sample HUNDRED_SQUARE_SIZE values for one axis of the addition table.

    The candidate list is duplicated HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR
    times before sampling without replacement, so a value can appear at
    most twice: needed because the default digit-1 range (1-9, nine
    distinct values) is smaller than the ten slots the table requires
    (mirrors nuts_calc.py's `100` square generation).
    """
    seed = nums * HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR
    return random.sample(seed, HUNDRED_SQUARE_SIZE)


def generate_hundred_square(nums_left: list[int], nums_top: list[int]) -> HundredSquareTable:
    return HundredSquareTable(
        left_values=sample_hundred_square_values(nums_left),
        top_values=sample_hundred_square_values(nums_top),
    )


def build_hundred_square_block_tex(table: HundredSquareTable, show_answer: bool) -> str:
    """
    Render one addition table as an (HUNDRED_SQUARE_SIZE+1)-square LaTeX
    tabular: a blank top-left corner, a shaded header row (table.top_values)
    and header column (table.left_values), and a HUNDRED_SQUARE_SIZE x
    HUNDRED_SQUARE_SIZE grid of data cells (left+top sums when show_answer,
    otherwise blank for the student to fill in).
    """
    column_spec = f">{{\\columncolor{{{HUNDRED_SQUARE_HEADER_COLOR}}}}}c|" + "c" * HUNDRED_SQUARE_SIZE
    header_cells = [''] + [str(value) for value in table.top_values]
    lines = [
        "\\begin{center}",
        f"\\begin{{tabular}}{{|{column_spec}|}}",
        "\\hline",
        f"\\rowcolor{{{HUNDRED_SQUARE_HEADER_COLOR}}} {' & '.join(header_cells)} \\\\",
        "\\hline",
    ]
    for left, answer_row in zip(table.left_values, table.answers):
        data_cells = [str(value) for value in answer_row] if show_answer else [''] * HUNDRED_SQUARE_SIZE
        lines.append(' & '.join([str(left)] + data_cells) + " \\\\")
        lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{center}")
    return "\n".join(lines)


def build_hundred_square_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[HundredSquareTable]]:
    """
    Generate real `100` addition tables and their blank/filled Page pairs.

    One table per page (`ini.page` controls the page count); `ini.rows`/
    `ini.columns`/`ini.with_bottom_answer` are accepted but unused for this
    command, matching nuts_calc.py's original `100` behavior (a single
    fixed-size 100-square table per page, no bottom answer strip).
    """
    nums_left = list(range(ini.a_min, ini.a_max + 1))
    nums_top = list(range(ini.b_min, ini.b_max + 1))

    blank_pages = []
    filled_pages = []
    pages_tables = []
    for _ in range(ini.page):
        table = generate_hundred_square(nums_left, nums_top)
        pages_tables.append(table)
        blank_pages.append(
            Page(blocks=[build_hundred_square_block_tex(table, show_answer=False)], columns=1, layout='block')
        )
        filled_pages.append(
            Page(blocks=[build_hundred_square_block_tex(table, show_answer=True)], columns=1, layout='block')
        )

    return blank_pages, filled_pages, pages_tables


def build_hundred_square_csv_rows(pages_tables: list[HundredSquareTable]) -> list[list[object]]:
    """One header row (`top_values`) plus one row per left value per page, each prefixed with the page number."""
    rows: list[list[object]] = []
    for page_number, table in enumerate(pages_tables, start=1):
        rows.append([page_number, ''] + table.top_values)
        for left, answer_row in zip(table.left_values, table.answers):
            rows.append([page_number, left] + answer_row)
    return rows


@dataclass
class KukuProblem:
    """One generated `99` (times-table / kuku) problem: a x b = c, with `a` fixed for a whole page."""
    index: int
    a: int
    b: int
    c: int


def generate_kuku_problems(a_value: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[KukuProblem]:
    """
    Generate `order` times-table problems for the fixed row `a_value`, starting at `start_index`.

    The multiplier `b` is drawn from the base sequence `1..order` -- an
    independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == '99'` branch (`nuts_calc.py:508-522`), which likewise ties the
    multiplier range to the page's row count rather than capping it at 9, so
    `b` can exceed 9 when `order > 9`. `descend` reverses that sequence
    (`order..1`); `shuffle` randomizes it after any `descend` reversal,
    matching nuts_calc.py's `num_list.reverse()` then `random.shuffle()`
    ordering (`nuts_calc.py:513-516`).
    """
    multipliers = list(range(1, order + 1))
    if descend:
        multipliers.reverse()
    if shuffle:
        random.shuffle(multipliers)
    return [
        KukuProblem(index=start_index + offset, a=a_value, b=b, c=a_value * b)
        for offset, b in enumerate(multipliers)
    ]


def build_kuku_block_tex(problem: KukuProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `99` problem: `n) $a \\times b = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times b$`,
    inferred from nuts_calc.py's `is_reverse` branch reordering `vals_c`
    ahead of `vals_a`/`vals_b` (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {problem.b}$"
    return f"{problem.index}) ${problem.a} \\times {problem.b} = {result_tex}$"


def build_kuku_page_pair(problems: list[KukuProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `99` problems."""
    blank_page = Page(
        blocks=[build_kuku_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_kuku_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_kuku_bottom_answer_tex(problems: list[KukuProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_kuku_csv_rows(pages_problems: list[list[KukuProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.b, problem.c])
    return rows


def build_kuku_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[KukuProblem]]]:
    """Generate real `99` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_kuku_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_kuku_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_kuku_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class AbcProblem:
    """
    One generated `aBc` problem: a random 4-digit sequence a/b/c/d (each
    0-9, displayed as `abcd`) converted to its value by adding the two
    digit-pairs `ab` (shifted one place, i.e. `x10`) and `cd`. This is the
    same digit-pair decomposition used by `ope --intermediate`'s
    mental-multiplication memo (`build_intermediate_memo`), drilled here on
    its own as a standalone conversion step (memo.md section 3: converting
    a 4-digit figure into its 3-digit result via digit-pair addition).
    """
    index: int
    a: int
    b: int
    c: int
    d: int

    @property
    def abcd_display(self) -> str:
        return f"{self.a}{self.b}{self.c}{self.d}"

    @property
    def answer(self) -> int:
        return (self.a * 10 + self.b) * 10 + (self.c * 10 + self.d)


def generate_abc_problems(order: int, start_index: int) -> list[AbcProblem]:
    """
    Generate `order` aBc problems starting at `start_index`.

    Each of a/b/c/d is drawn independently from 0..ABC_DIGIT_MAX -- an
    independent reimplementation of nuts_calc.py's `get_aBc_data`
    (`nuts_calc.py:548-587`), which draws the same four digits from the
    same range. Unlike that implementation, `AbcProblem.abcd_display`
    always renders all four digits (`f"{a}{b}{c}{d}"`) instead of only
    zero-padding the single 3-character case (`nuts_calc.py:577-578` only
    handles `len(str(abcd)) == 3`, leaving shorter results un-padded).
    """
    seed = list(range(ABC_DIGIT_MAX + 1))
    problems = []
    for offset in range(order):
        a = random.choice(seed)
        b = random.choice(seed)
        c = random.choice(seed)
        d = random.choice(seed)
        problems.append(AbcProblem(index=start_index + offset, a=a, b=b, c=c, d=d))
    return problems


def build_abc_block_tex(problem: AbcProblem, show_answer: bool) -> str:
    """Render one `aBc` problem: `n) $abcd \\Rightarrow ____$`, filled with the converted answer when show_answer."""
    result_tex = str(problem.answer) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) ${problem.abcd_display} \\Rightarrow {result_tex}$"


def build_abc_page_pair(problems: list[AbcProblem], columns: int) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `aBc` problems."""
    blank_page = Page(
        blocks=[build_abc_block_tex(problem, show_answer=False) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_abc_block_tex(problem, show_answer=True) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_abc_bottom_answer_tex(problems: list[AbcProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.answer}" for problem in problems)


def build_abc_csv_rows(pages_problems: list[list[AbcProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index,
                problem.a, problem.b, problem.c, problem.d, problem.answer,
            ])
    return rows


def build_abc_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[AbcProblem]]]:
    """Generate real `aBc` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_abc_problems(order, start_index)
        blank_page, filled_page = build_abc_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_abc_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class SquProblem:
    """One generated `squ` (square numbers) problem: a x a = c."""
    index: int
    a: int
    c: int


def generate_squ_problems(start_num: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[SquProblem]:
    """
    Generate `order` square-number problems starting from `start_num`, with problem numbering starting at `start_index`.

    An independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == 'squ'` branch (`nuts_calc.py:508-526,541-542`): the base
    sequence `start_num..start_num+order-1` is squared (`a = a`, `c = a * a`
    -- `b` is always equal to `a`, so it is not stored separately).
    `descend` reverses that sequence (`start_num+order-1..start_num`);
    `shuffle` randomizes it after any `descend` reversal, matching
    nuts_calc.py's `num_list.reverse()` then `random.shuffle()` ordering.
    """
    sequence = list(range(start_num, start_num + order))
    if descend:
        sequence.reverse()
    if shuffle:
        random.shuffle(sequence)
    return [
        SquProblem(index=start_index + offset, a=a, c=a * a)
        for offset, a in enumerate(sequence)
    ]


def build_squ_block_tex(problem: SquProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `squ` problem: `n) $a \\times a = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times a$`,
    mirroring `build_kuku_block_tex`'s handling of nuts_calc.py's
    `is_reverse` branch (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {problem.a}$"
    return f"{problem.index}) ${problem.a} \\times {problem.a} = {result_tex}$"


def build_squ_page_pair(problems: list[SquProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `squ` problems."""
    blank_page = Page(
        blocks=[build_squ_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_squ_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_squ_bottom_answer_tex(problems: list[SquProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_squ_csv_rows(pages_problems: list[list[SquProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.c])
    return rows


def build_squ_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[SquProblem]]]:
    """Generate real `squ` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_squ_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_squ_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_squ_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


def _ope_uses_multi_term(ini: argparse.Namespace) -> bool:
    """Whether `ope` should use the flat multi-term path (any term-count/mixed-operator option given)."""
    return (
        ini.terms_min != TERM_COUNT_FLOOR_DEFAULT
        or ini.terms_max != TERM_COUNT_FLOOR_DEFAULT
        or ini.mixed_operators
    )


def build_ope_pages(
        ini: argparse.Namespace
    ) -> tuple[
        list[Page], list[Page],
        list[list[OpeProblem]] | list[list[TreeOpeProblem]]
        | list[list[MultiTermOpeProblem]] | list[list[MissingValueProblem]],
    ]:
    """
    Generate real `ope` problems and their blank/filled Page pairs for every page.

    Delegates to build_tree_ope_pages() when --use-parentheses is set, to
    build_missing_value_pages() when --missing-value is set, and to
    build_multi_term_ope_pages() when any term-count/--mixed-operators
    option is given, since each mode uses a distinct problem shape and
    generation/rendering path from plain 2-term `ope` (and are mutually
    exclusive, enforced in _init()). --use-parentheses always implies
    terms_min/terms_max >= 3 (floor-clamped in _init()), so the legacy
    2-term path below is reached only when no new option is given at all --
    a default `ope` invocation runs through this exact unmodified code.
    """
    if ini.use_parentheses:
        return build_tree_ope_pages(ini)

    if ini.missing_value:
        return build_missing_value_pages(ini)

    if _ope_uses_multi_term(ini):
        return build_multi_term_ope_pages(ini)

    nums_a = list(range(ini.a_min, ini.a_max + 1))
    nums_b = list(range(ini.b_min, ini.b_max + 1))
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_ope_problems(
            nums_a, nums_b, ini.operator, order, start_index,
            ini.a_decimal_places, ini.b_decimal_places, ini.carry_mode,
            ini.remainder_mode,
        )
        blank_page, filled_page = build_ope_page_pair(problems, ini.columns, ini.vertical, ini.intermediate)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_ope_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass
class PiProblem:
    """One generated `pi` (multiplication by pi) problem: a x PI_MULTIPLIER = c."""
    index: int
    a: int
    c: float


def generate_pi_problems(start_num: int, order: int, start_index: int, descend: bool, shuffle: bool) -> list[PiProblem]:
    """
    Generate `order` pi-multiplication problems starting from `start_num`, with problem numbering starting at `start_index`.

    An independent reimplementation of nuts_calc.py's `get_fixed_format_data`
    `mode == 'pi'` branch (`nuts_calc.py:508-522,527-530,541-542`): the base
    sequence `start_num..start_num+order-1` is multiplied by `PI_MULTIPLIER`
    (`a = a`, `c = a * PI_MULTIPLIER` -- `b` is always `PI_MULTIPLIER`, so it
    is not stored separately). `descend` reverses that sequence
    (`start_num+order-1..start_num`); `shuffle` randomizes it after any
    `descend` reversal, matching nuts_calc.py's `num_list.reverse()` then
    `random.shuffle()` ordering (same as `generate_squ_problems`).

    `c` is rounded to 2 decimal places: `PI_MULTIPLIER` (3.14) has 2 decimal
    digits, so `a * PI_MULTIPLIER` is mathematically always exact to 2
    decimals, but IEEE 754 float multiplication produces artifacts for some
    `a` (e.g. `5 * 3.14 == 15.700000000000001`) that nuts_calc.py renders
    verbatim; rounding avoids surfacing that artifact in the printed drill.
    """
    sequence = list(range(start_num, start_num + order))
    if descend:
        sequence.reverse()
    if shuffle:
        random.shuffle(sequence)
    return [
        PiProblem(index=start_index + offset, a=a, c=round(a * PI_MULTIPLIER, 2))
        for offset, a in enumerate(sequence)
    ]


def build_pi_block_tex(problem: PiProblem, show_answer: bool, reverse: bool) -> str:
    """
    Render one `pi` problem: `n) $a \\times 3.14 = c$` (blank hides `c`).

    `reverse` swaps the equation side order to `n) $c = a \\times 3.14$`,
    mirroring `build_squ_block_tex`'s handling of nuts_calc.py's
    `is_reverse` branch (`nuts_calc.py:543-545`); the blanked value is
    always `c` regardless of which side it renders on.
    """
    result_tex = str(problem.c) if show_answer else BLANK_ANSWER_TEX
    if reverse:
        return f"{problem.index}) ${result_tex} = {problem.a} \\times {PI_MULTIPLIER}$"
    return f"{problem.index}) ${problem.a} \\times {PI_MULTIPLIER} = {result_tex}$"


def build_pi_page_pair(problems: list[PiProblem], columns: int, reverse: bool) -> tuple[Page, Page]:
    """Build the (blank, filled) Page pair for one page's worth of `pi` problems."""
    blank_page = Page(
        blocks=[build_pi_block_tex(problem, show_answer=False, reverse=reverse) for problem in problems],
        columns=columns,
    )
    filled_page = Page(
        blocks=[build_pi_block_tex(problem, show_answer=True, reverse=reverse) for problem in problems],
        columns=columns,
    )
    return blank_page, filled_page


def build_pi_bottom_answer_tex(problems: list[PiProblem]) -> str:
    return ' \\quad '.join(f"({problem.index}) {problem.c}" for problem in problems)


def build_pi_csv_rows(pages_problems: list[list[PiProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([page_number, problem.index, problem.a, problem.c])
    return rows


def build_pi_pages(ini: argparse.Namespace) -> tuple[list[Page], list[Page], list[list[PiProblem]]]:
    """Generate real `pi` problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns

    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        start_index = (page_number - 1) * order + 1
        problems = generate_pi_problems(ini.a_value, order, start_index, ini.descend, ini.shuffle)
        blank_page, filled_page = build_pi_page_pair(problems, ini.columns, ini.reverse)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)

    if ini.with_bottom_answer:
        for problems, blank_page in zip(pages_problems, blank_pages):
            blank_page.bottom_answer_tex = build_pi_bottom_answer_tex(problems)

    return blank_pages, filled_pages, pages_problems


@dataclass(frozen=True)
class FractionOperand:
    """A displayed fraction whose unreduced numerator/denominator are retained."""
    numerator: int
    denominator: int

    @property
    def value(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True)
class FractionProblem:
    """One exact fraction-arithmetic problem."""
    index: int
    a: FractionOperand
    b: FractionOperand
    operator: str
    c: Fraction


def digit_range(digits: int) -> tuple[int, int]:
    """Return the positive integer range having exactly ``digits`` digits."""
    return (1 if digits == 1 else 10 ** (digits - 1), 10 ** digits - 1)


def random_fraction_operand(
        numerator_digits: int, denominator_digits: int, proper: bool,
        denominator: int | None = None,
    ) -> FractionOperand:
    numerator_min, numerator_max = digit_range(numerator_digits)
    denominator_min, denominator_max = digit_range(denominator_digits)
    denominator_min = max(2, denominator_min)
    chosen_denominator = denominator or random.randint(denominator_min, denominator_max)
    if proper:
        numerator_max = min(numerator_max, chosen_denominator - 1)
    if numerator_min > numerator_max:
        raise ValueError("No fraction operand satisfies the requested digit and proper-fraction constraints.")
    return FractionOperand(random.randint(numerator_min, numerator_max), chosen_denominator)


def calculate_fraction(a: Fraction, b: Fraction, operator: str) -> Fraction:
    """Apply one supported operator to two exact fraction values."""
    if operator == 'add':
        return a + b
    if operator == 'sub':
        return a - b
    if operator == 'mul':
        return a * b
    return a / b


def generate_fraction_problems(
        numerator_digits: int, denominator_digits: int, operators: list[str],
        order: int, start_index: int, same_denominator: bool,
        proper_operands: bool, proper_result: bool,
        different_denominators: bool = False,
    ) -> list[FractionProblem]:
    """Generate exact fraction problems satisfying the requested constraints."""
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    denominator_min, denominator_max = digit_range(denominator_digits)
    denominator_min = max(2, denominator_min)
    problems = []
    for offset in range(order):
        operator = random.choice(effective_operators)
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            common_denominator = (
                random.randint(denominator_min, denominator_max)
                if same_denominator else None
            )
            try:
                a = random_fraction_operand(
                    numerator_digits, denominator_digits, proper_operands,
                    common_denominator,
                )
                b = random_fraction_operand(
                    numerator_digits, denominator_digits, proper_operands,
                    common_denominator,
                )
            except ValueError:
                continue
            if different_denominators and a.denominator == b.denominator:
                continue
            c = calculate_fraction(a.value, b.value, operator)
            if c <= 0:
                continue
            if proper_result and c >= 1:
                continue
            problems.append(FractionProblem(start_index + offset, a, b, operator, c))
            break
        else:
            raise ValueError("Unable to generate fraction problems with the requested constraints.")
    return problems


def fraction_to_tex(value: Fraction | FractionOperand) -> str:
    """Render an exact or display-preserving fraction as LaTeX."""
    numerator = value.numerator
    denominator = value.denominator
    if denominator == 1:
        return str(numerator)
    return f"\\frac{{{numerator}}}{{{denominator}}}"


def build_fraction_block_tex(problem: FractionProblem, show_answer: bool) -> str:
    symbol = OPERATOR_TEX_SYMBOLS[problem.operator]
    result_tex = fraction_to_tex(problem.c) if show_answer else BLANK_ANSWER_TEX
    return (
        f"{problem.index}) $\\displaystyle {fraction_to_tex(problem.a)} {symbol} "
        f"{fraction_to_tex(problem.b)} = {result_tex}$"
    )


def build_fraction_page_pair(problems: list[FractionProblem], columns: int) -> tuple[Page, Page]:
    return (
        Page([build_fraction_block_tex(problem, False) for problem in problems], columns),
        Page([build_fraction_block_tex(problem, True) for problem in problems], columns),
    )


def build_fraction_bottom_answer_tex(problems: list[FractionProblem]) -> str:
    return ' \\quad '.join(
        f"({problem.index}) $\\displaystyle {fraction_to_tex(problem.c)}$"
        for problem in problems
    )


def build_fraction_csv_rows(pages_problems: list[list[FractionProblem]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index,
                problem.a.numerator, problem.a.denominator, problem.operator,
                problem.b.numerator, problem.b.denominator,
                problem.c.numerator, problem.c.denominator,
            ])
    return rows


def build_fraction_pages(
        ini: argparse.Namespace,
    ) -> tuple[list[Page], list[Page], list[list[FractionProblem]]]:
    order = ini.rows * ini.columns
    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        problems = generate_fraction_problems(
            ini.numerator_digits, ini.denominator_digits, ini.operator, order,
            (page_number - 1) * order + 1, ini.same_denominator,
            ini.proper_operands, ini.proper_result, ini.different_denominators,
        )
        blank_page, filled_page = build_fraction_page_pair(problems, ini.columns)
        if ini.with_bottom_answer:
            blank_page.bottom_answer_tex = build_fraction_bottom_answer_tex(problems)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)
    return blank_pages, filled_pages, pages_problems


COMPARISON_FORMS = ('proper', 'improper', 'mixed')


@dataclass(frozen=True)
class FractionComparisonOperand:
    """One displayed comparison operand, optionally written as a mixed number."""
    numerator: int
    denominator: int
    whole: int = 0

    @property
    def value(self) -> Fraction:
        return Fraction(self.whole * self.denominator + self.numerator, self.denominator)


@dataclass(frozen=True)
class FractionComparisonProblem:
    """One fraction comparison whose answer is the relation symbol."""
    index: int
    a: FractionComparisonOperand
    b: FractionComparisonOperand

    @property
    def relation(self) -> str:
        return '<' if self.a.value < self.b.value else '>'


def random_comparison_operand(
        form: str, numerator_digits: int, denominator_digits: int,
    ) -> FractionComparisonOperand:
    """Create one proper, improper, or mixed-number comparison operand."""
    if form == 'mix':
        form = random.choice(COMPARISON_FORMS)
    numerator_min, numerator_max = digit_range(numerator_digits)
    denominator_min, denominator_max = digit_range(denominator_digits)
    denominator_min = max(2, denominator_min)
    denominator = random.randint(denominator_min, denominator_max)

    if form in ('proper', 'mixed'):
        numerator_max = min(numerator_max, denominator - 1)
        if numerator_min > numerator_max:
            raise ValueError(f"No {form} fraction satisfies the requested digit constraints.")
        numerator = random.randint(numerator_min, numerator_max)
        return FractionComparisonOperand(numerator, denominator, random.randint(1, 9) if form == 'mixed' else 0)

    numerator_min = max(numerator_min, denominator + 1)
    if numerator_min > numerator_max:
        raise ValueError("No improper fraction satisfies the requested digit constraints.")
    return FractionComparisonOperand(random.randint(numerator_min, numerator_max), denominator)


def generate_fraction_comparison_problems(
        pattern: str, a_form: str, b_form: str, numerator_digits: int,
        denominator_digits: int, order: int, start_index: int,
    ) -> list[FractionComparisonProblem]:
    """Generate non-equal comparison problems matching a display pattern."""
    problems = []
    for offset in range(order):
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            try:
                a = random_comparison_operand(a_form, numerator_digits, denominator_digits)
                b = random_comparison_operand(b_form, numerator_digits, denominator_digits)
            except ValueError:
                continue
            if a.value == b.value:
                continue
            if pattern == 'same-denominator':
                if a.denominator != b.denominator or a.numerator == b.numerator:
                    continue
            elif pattern == 'same-numerator':
                if a.numerator != b.numerator or a.denominator == b.denominator:
                    continue
            elif pattern == 'different-denominators':
                if a.denominator == b.denominator:
                    continue
            else:
                raise ValueError(f"Unknown comparison pattern: {pattern}")
            problems.append(FractionComparisonProblem(start_index + offset, a, b))
            break
        else:
            raise ValueError(
                "Unable to generate fraction comparison problems with the requested "
                "pattern, forms, and digit constraints."
            )
    return problems


def comparison_operand_to_tex(operand: FractionComparisonOperand) -> str:
    """Render a comparison operand, retaining its requested fraction form."""
    fraction_tex = f"\\frac{{{operand.numerator}}}{{{operand.denominator}}}"
    return f"{operand.whole}{fraction_tex}" if operand.whole else fraction_tex


def build_fraction_comparison_block_tex(problem: FractionComparisonProblem, show_answer: bool) -> str:
    relation_tex = problem.relation if show_answer else BOXED_BLANK_TEX
    return (
        f"{problem.index}) $\\displaystyle {comparison_operand_to_tex(problem.a)} "
        f"{relation_tex} {comparison_operand_to_tex(problem.b)}$"
    )


def build_fraction_comparison_page_pair(
        problems: list[FractionComparisonProblem], columns: int,
    ) -> tuple[Page, Page]:
    return (
        Page([build_fraction_comparison_block_tex(problem, False) for problem in problems], columns),
        Page([build_fraction_comparison_block_tex(problem, True) for problem in problems], columns),
    )


def build_fraction_comparison_csv_rows(
        pages_problems: list[list[FractionComparisonProblem]],
    ) -> list[list[object]]:
    return [
        [
            page_number, problem.index,
            problem.a.whole, problem.a.numerator, problem.a.denominator,
            problem.relation,
            problem.b.whole, problem.b.numerator, problem.b.denominator,
        ]
        for page_number, problems in enumerate(pages_problems, start=1)
        for problem in problems
    ]


def build_fraction_comparison_pages(
        ini: argparse.Namespace,
    ) -> tuple[list[Page], list[Page], list[list[FractionComparisonProblem]]]:
    order = ini.rows * ini.columns
    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        problems = generate_fraction_comparison_problems(
            ini.comparison_pattern, ini.a_fraction_form, ini.b_fraction_form,
            ini.numerator_digits, ini.denominator_digits, order,
            (page_number - 1) * order + 1,
        )
        blank_page, filled_page = build_fraction_comparison_page_pair(problems, ini.columns)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)
    return blank_pages, filled_pages, pages_problems


@dataclass(frozen=True)
class MixedOperand:
    """One "mixed"-command operand: its kind, ready-to-embed TeX, and exact value."""
    kind: str  # 'int' | 'decimal' | 'fraction'
    display: str
    value: Fraction


@dataclass(frozen=True)
class MixedProblem:
    """One "mixed" (int/decimal/fraction) arithmetic problem, 2+ terms."""
    index: int
    operands: list[MixedOperand]
    operators: list[str]
    mixed: bool
    result: Fraction


def random_mixed_operand(
        kind: str, numerator_digits: int, denominator_digits: int, decimal_places: int,
    ) -> MixedOperand:
    """
    Generate one operand of the given kind, all resolved to an exact
    Fraction value (never a float):
    - 'int': a plain integer, digit-range sized by numerator_digits.
    - 'decimal': a scaled integer (same digit range) divided by
      10^decimal_places -- an exact, finite decimal by construction, the
      same technique format_decimal_value/OpeProblem use for `ope`.
    - 'fraction': reuses random_fraction_operand (frac command).
    """
    if kind == 'int':
        value = random.randint(*digit_range(numerator_digits))
        return MixedOperand('int', str(value), Fraction(value))
    if kind == 'decimal':
        scaled = random.randint(*digit_range(numerator_digits))
        return MixedOperand('decimal', format_decimal_value(scaled, decimal_places), Fraction(scaled, 10 ** decimal_places))
    fraction_operand = random_fraction_operand(numerator_digits, denominator_digits, proper=False)
    return MixedOperand('fraction', fraction_to_tex(fraction_operand), fraction_operand.value)


def generate_mixed_problems(
        a_kinds: list[str], b_kinds: list[str], operators: list[str], mixed: bool,
        numerator_digits: int, denominator_digits: int, decimal_places: int,
        terms_min: int, terms_max: int, order: int, start_index: int,
    ) -> list[MixedProblem]:
    """
    Generate `order` flat (non-parenthesized) N-term "mixed" problems, each
    independently drawing its term count from [terms_min, terms_max] --
    mirrors generate_multi_term_ope_problems's shape/retry convention, but
    operands are MixedOperand (int/decimal/fraction) resolved to exact
    Fraction values and evaluated via MIXED_STAGE_FUNCTIONS, so every
    intermediate and final result is exact (no floats, no infinite
    decimals): a division whose Fraction result doesn't terminate as a
    decimal is still rendered exactly as a fraction (see
    build_mixed_block_tex), never coerced into decimal notation.

    The first term is drawn from a_kinds, every later term from b_kinds
    (mirrors generate_multi_term_ope_problems's nums_a/nums_b convention).
    """
    effective_operators = MIX_OPERATORS if 'mix' in operators else operators
    problems = []
    for offset in range(order):
        term_count = random.randint(terms_min, terms_max)
        gap_count = term_count - 1
        for _ in range(MAX_OPERAND_RETRY_ATTEMPTS):
            operands = [random_mixed_operand(random.choice(a_kinds), numerator_digits, denominator_digits, decimal_places)]
            operands += [
                random_mixed_operand(random.choice(b_kinds), numerator_digits, denominator_digits, decimal_places)
                for _ in range(gap_count)
            ]
            values = [operand.value for operand in operands]
            if mixed:
                problem_operators = [random.choice(effective_operators) for _ in range(gap_count)]
                result = evaluate_mixed_expression(values, problem_operators, MIXED_STAGE_FUNCTIONS)
            else:
                shared_operator = random.choice(effective_operators)
                problem_operators = [shared_operator] * gap_count
                result = evaluate_left_to_right(values, problem_operators, MIXED_STAGE_FUNCTIONS)
            if result is not None:
                problems.append(MixedProblem(
                    index=start_index + offset, operands=operands,
                    operators=problem_operators, mixed=mixed, result=result,
                ))
                break
        else:
            raise ValueError(
                f"No valid {term_count}-term mixed expression found within the requested kinds/digits (mixed={mixed})."
            )
    return problems


def build_mixed_expression_text(problem: MixedProblem) -> str:
    """Render-agnostic expression string for CSV output, e.g. "3 mul 0.5 div 2/3"."""
    parts = [problem.operands[0].display]
    for operand, operator in zip(problem.operands[1:], problem.operators):
        parts += [operator, operand.display]
    return ' '.join(parts)


def build_mixed_block_tex(problem: MixedProblem, show_answer: bool) -> str:
    """
    Render one flat multi-term "mixed" problem: `n) $a op1 b op2 c ... =
    result$` (no parentheses). The answer is always an exact reduced
    fraction (fraction_to_tex(Fraction)), never decimal notation -- see
    MIXED_STAGE_FUNCTIONS's div and this file's decimal-arithmetic design
    note (no infinite/repeating decimals anywhere in generated output).
    """
    parts = [problem.operands[0].display]
    for operand, operator in zip(problem.operands[1:], problem.operators):
        parts += [OPERATOR_TEX_SYMBOLS[operator], operand.display]
    result_tex = fraction_to_tex(problem.result) if show_answer else BLANK_ANSWER_TEX
    return f"{problem.index}) $\\displaystyle {' '.join(parts)} = {result_tex}$"


def build_mixed_page_pair(problems: list[MixedProblem], columns: int) -> tuple[Page, Page]:
    return (
        Page([build_mixed_block_tex(problem, False) for problem in problems], columns),
        Page([build_mixed_block_tex(problem, True) for problem in problems], columns),
    )


def build_mixed_bottom_answer_tex(problems: list[MixedProblem]) -> str:
    return ' \\quad '.join(
        f"({problem.index}) $\\displaystyle {fraction_to_tex(problem.result)}$"
        for problem in problems
    )


def build_mixed_csv_rows(pages_problems: list[list[MixedProblem]]) -> list[list[object]]:
    """One row per problem: [page_number, index, terms, mixed, expression, result_numerator, result_denominator]."""
    rows: list[list[object]] = []
    for page_number, problems in enumerate(pages_problems, start=1):
        for problem in problems:
            rows.append([
                page_number, problem.index, len(problem.operands), problem.mixed,
                build_mixed_expression_text(problem),
                problem.result.numerator, problem.result.denominator,
            ])
    return rows


def build_mixed_pages(
        ini: argparse.Namespace,
    ) -> tuple[list[Page], list[Page], list[list[MixedProblem]]]:
    """Generate real "mixed" problems and their blank/filled Page pairs for every page."""
    order = ini.rows * ini.columns
    blank_pages = []
    filled_pages = []
    pages_problems = []
    for page_number in range(1, ini.page + 1):
        problems = generate_mixed_problems(
            ini.a_kind, ini.b_kind, ini.operator, ini.mixed_operators,
            ini.numerator_digits, ini.denominator_digits, ini.decimal_places,
            ini.terms_min, ini.terms_max, order, (page_number - 1) * order + 1,
        )
        blank_page, filled_page = build_mixed_page_pair(problems, ini.columns)
        if ini.with_bottom_answer:
            blank_page.bottom_answer_tex = build_mixed_bottom_answer_tex(problems)
        pages_problems.append(problems)
        blank_pages.append(blank_page)
        filled_pages.append(filled_page)
    return blank_pages, filled_pages, pages_problems


def main(ini: argparse.Namespace) -> None:
    if shutil.which('pdflatex') is None:
        failure(
            "pdflatex not found. Install a LaTeX distribution first "
            "(e.g. `sudo apt-get install texlive-latex-base texlive-latex-extra`)."
        )

    ope_pages_problems: list[list[OpeProblem]] | None = None
    tree_ope_pages_problems: list[list[TreeOpeProblem]] | None = None
    multi_term_ope_pages_problems: list[list[MultiTermOpeProblem]] | None = None
    missing_value_pages_problems: list[list[MissingValueProblem]] | None = None
    com_pages_problems: list[list[ComProblem]] | None = None
    hundred_square_pages_tables: list[HundredSquareTable] | None = None
    kuku_pages_problems: list[list[KukuProblem]] | None = None
    abc_pages_problems: list[list[AbcProblem]] | None = None
    squ_pages_problems: list[list[SquProblem]] | None = None
    pi_pages_problems: list[list[PiProblem]] | None = None
    fraction_pages_problems: list[list[FractionProblem]] | None = None
    comparison_pages_problems: list[list[FractionComparisonProblem]] | None = None
    mixed_pages_problems: list[list[MixedProblem]] | None = None
    if ini.command == 'ope' and ini.use_parentheses:
        blank_pages, filled_pages, tree_ope_pages_problems = build_ope_pages(ini)
    elif ini.command == 'ope' and ini.missing_value:
        blank_pages, filled_pages, missing_value_pages_problems = build_ope_pages(ini)
    elif ini.command == 'ope' and _ope_uses_multi_term(ini):
        blank_pages, filled_pages, multi_term_ope_pages_problems = build_ope_pages(ini)
    elif ini.command == 'ope':
        blank_pages, filled_pages, ope_pages_problems = build_ope_pages(ini)
    elif ini.command == 'com':
        blank_pages, filled_pages, com_pages_problems = build_com_pages(ini)
    elif ini.command == '100':
        blank_pages, filled_pages, hundred_square_pages_tables = build_hundred_square_pages(ini)
    elif ini.command == '99':
        blank_pages, filled_pages, kuku_pages_problems = build_kuku_pages(ini)
    elif ini.command == 'aBc':
        blank_pages, filled_pages, abc_pages_problems = build_abc_pages(ini)
    elif ini.command == 'squ':
        blank_pages, filled_pages, squ_pages_problems = build_squ_pages(ini)
    elif ini.command == 'pi':
        blank_pages, filled_pages, pi_pages_problems = build_pi_pages(ini)
    elif ini.command == 'mixed':
        blank_pages, filled_pages, mixed_pages_problems = build_mixed_pages(ini)
    elif ini.command == 'compare':
        blank_pages, filled_pages, comparison_pages_problems = build_fraction_comparison_pages(ini)
    else:
        blank_pages, filled_pages, fraction_pages_problems = build_fraction_pages(ini)

    outfile_basename, _ = os.path.splitext(ini.out_file)
    outfile_read = outfile_basename + '_read.pdf'
    outfile_csv = outfile_basename + '.csv'

    if ini.merge:
        tex_source = build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='merge')
        compile_tex(tex_source, ini.out_file)
    else:
        compile_tex(build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='blank'), ini.out_file)
        compile_tex(build_document_tex(ini.paper_size, blank_pages, filled_pages, mode='filled'), outfile_read)

    if ini.csv:
        if ope_pages_problems is not None:
            rows = build_ope_csv_rows(ope_pages_problems)
        elif tree_ope_pages_problems is not None:
            rows = build_tree_ope_csv_rows(tree_ope_pages_problems)
        elif multi_term_ope_pages_problems is not None:
            rows = build_multi_term_ope_csv_rows(multi_term_ope_pages_problems)
        elif missing_value_pages_problems is not None:
            rows = build_missing_value_csv_rows(missing_value_pages_problems)
        elif com_pages_problems is not None:
            rows = build_com_csv_rows(com_pages_problems)
        elif hundred_square_pages_tables is not None:
            rows = build_hundred_square_csv_rows(hundred_square_pages_tables)
        elif kuku_pages_problems is not None:
            rows = build_kuku_csv_rows(kuku_pages_problems)
        elif abc_pages_problems is not None:
            rows = build_abc_csv_rows(abc_pages_problems)
        elif squ_pages_problems is not None:
            rows = build_squ_csv_rows(squ_pages_problems)
        elif pi_pages_problems is not None:
            rows = build_pi_csv_rows(pi_pages_problems)
        elif mixed_pages_problems is not None:
            rows = build_mixed_csv_rows(mixed_pages_problems)
        elif comparison_pages_problems is not None:
            rows = build_fraction_comparison_csv_rows(comparison_pages_problems)
        else:
            rows = build_fraction_csv_rows(fraction_pages_problems)
        write_csv(rows, outfile_csv)

    print("export PDF")
    print("All done")


if __name__ == '__main__':
    main(_init())
