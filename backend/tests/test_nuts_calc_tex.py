"""End-to-end regression tests for nuts_calc_tex.py (Phase 1 foundation #20;
`ope` command Phase 2 #21; `com` command Phase 3 #22; `99` command Phase 5
#24; `aBc` command Phase 6 #25; `squ` command Phase 7 #26; `pi` command
Phase 8 #27; fraction arithmetic #65; `ope --use-parentheses` #67;
`ope --missing-value` #69; `evenodd`/`multiples`/`divisors` #94; `lcm`/`gcd`
#95; and `simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` #96).

nuts_calc_tex.py has zero code dependency on nuts_calc.py, so these tests
run it as a real subprocess, independent of tests/test_nuts_calc_cli.py.
All tests are skipped when `pdflatex` is not on PATH, since this module
requires a LaTeX distribution. Pure-Python `ope`/`com`/`99`/`aBc`/`squ`/`pi`/
`evenodd`/`multiples`/`divisors`/`lcm`/`gcd`/`simplify`/`commondenom`/
`frac2dec`/`dec2frac`/`divfrac` generation logic that doesn't need pdflatex
is covered separately in test_nuts_calc_tex_ope_generation.py,
test_nuts_calc_tex_com_generation.py, test_nuts_calc_tex_kuku_generation.py,
test_nuts_calc_tex_abc_generation.py, test_nuts_calc_tex_squ_generation.py,
test_nuts_calc_tex_pi_generation.py, test_nuts_calc_tex_evenodd_generation.py,
test_nuts_calc_tex_multiples_generation.py,
test_nuts_calc_tex_divisors_generation.py,
test_nuts_calc_tex_lcm_gcd_generation.py, and
test_nuts_calc_tex_conversion_generation.py.
"""

import math
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from nuts_calc_tex import (
    Page,
    addition_has_carry,
    build_block_grid_tex,
    build_inline_grid_tex,
    build_page_header_tex,
    build_page_tex,
    build_preamble_tex,
    build_tabular_grid_tex,
    evaluate_mixed_expression,
    subtraction_has_borrow,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
NUTS_CALC_TEX = BACKEND_DIR / "nuts_calc_tex.py"

CLI_TIMEOUT_SECONDS = 60

pytestmark = pytest.mark.skipif(
    shutil.which("pdflatex") is None,
    reason="nuts_calc_tex.py requires a LaTeX distribution (pdflatex) on PATH",
)


def test_inline_grid_places_sequential_blocks_down_each_column() -> None:
    tex = build_inline_grid_tex(["1)", "2)", "3)", "4)"], columns=2)

    assert tex == (
        "\\vfill\n"
        "\\noindent\\begin{tabular}{>{\\centering\\arraybackslash}p{\\dimexpr(\\textwidth-4\\tabcolsep)/2\\relax}"
        ">{\\centering\\arraybackslash}p{\\dimexpr(\\textwidth-4\\tabcolsep)/2\\relax}}\n"
        "1) & 3)\\\\\n"
        "\\end{tabular}\n"
        "\\vfill\n"
        "\\noindent\\begin{tabular}{>{\\centering\\arraybackslash}p{\\dimexpr(\\textwidth-4\\tabcolsep)/2\\relax}"
        ">{\\centering\\arraybackslash}p{\\dimexpr(\\textwidth-4\\tabcolsep)/2\\relax}}\n"
        "2) & 4)\\\\\n"
        "\\end{tabular}"
    )


def test_preamble_reserves_a_40mm_footer_area() -> None:
    tex = build_preamble_tex("A4")

    assert "margin=15mm,top=20mm,bottom=40mm" in tex
    assert "\\addtolength{\\footskip}{20mm}" in tex


def test_page_header_omits_name_field_by_default() -> None:
    tex = build_page_header_tex()

    assert "Name:" not in tex
    assert tex == build_page_header_tex(with_name_field=False)


def test_page_header_includes_name_field_when_requested() -> None:
    tex = build_page_header_tex(with_name_field=True)

    assert "Name: \\underline{\\hspace{8cm}}" in tex


def test_inline_grid_fills_an_incomplete_row_with_an_empty_cell() -> None:
    tex = build_inline_grid_tex(["1)", "2)", "3)"], columns=2)

    assert "2) & " in tex
    assert tex.count("\\begin{tabular}{") == 2


def test_inline_grid_uses_equal_width_cells_for_four_columns() -> None:
    tex = build_inline_grid_tex(["1)", "2)", "3)", "4)"], columns=4)

    expected_column = ">{\\centering\\arraybackslash}p{\\dimexpr(\\textwidth-8\\tabcolsep)/4\\relax}"
    assert expected_column * 4 in tex


def test_block_grid_keeps_a_self_contained_table_outside_inline_cells() -> None:
    block_tex = "\\begin{center}\\begin{tabular}{c}100\\end{tabular}\\end{center}"

    tex = build_page_tex(Page(blocks=[block_tex], layout="block"))

    assert build_block_grid_tex([block_tex]) in tex
    assert "\\begin{tabular}{>{\\centering\\arraybackslash}p" not in tex


def test_tabular_grid_places_sequential_blocks_down_each_column() -> None:
    tex = build_tabular_grid_tex(["1)", "2)", "3)", "4)"], columns=2)

    assert "1) & 3)" in tex
    assert "2) & 4)" in tex


@pytest.fixture
def run_tex_cli(tmp_path: Path):
    """Run nuts_calc_tex.py as a subprocess, with tmp_path as the working
    directory so relative --out-file paths land in an isolated, auto-cleaned
    directory.

    Defaults NUTS_CALC_TEX_ENGINE to pdflatex (~9x faster than the
    production default, lualatex, issue #186): none of these generation
    tests exercise CJK output, and lualatex-specific behavior is covered
    separately in test_nuts_calc_tex_lualatex_engine.py. A caller-set
    NUTS_CALC_TEX_ENGINE is left untouched.
    """

    def _run(*args: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.setdefault("NUTS_CALC_TEX_ENGINE", "pdflatex")
        return subprocess.run(
            [sys.executable, str(NUTS_CALC_TEX), *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
            env=env,
        )

    return _run


def _assert_is_pdf(path: Path) -> None:
    assert path.exists(), f"expected PDF at {path}"
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


def _pdf_page_count(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True, check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", maxsplit=1)[1].strip())
    raise AssertionError(f"pdfinfo did not report a page count for {path}")


def test_cli_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-r", "3", "-c", "2", "-p", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.parametrize("paper_size", ["A3", "A4", "B5", "a4l"])
def test_cli_runs_for_each_paper_size(run_tex_cli, tmp_path, paper_size):
    result = run_tex_cli(paper_size, "ope", "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_merge_produces_single_pdf_without_read_file(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-m", "-r", "2", "-c", "2", "-p", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    assert not (tmp_path / "result_read.pdf").exists()


def test_cli_csv_flag_writes_csv_with_one_row_per_problem(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-r", "3", "-c", "2", "-p", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    assert csv_path.exists()
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 3 * 2 * 2  # rows * columns * pages


def test_cli_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_with_name_field_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-r", "2", "-c", "2", "--with-name-field", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_rejects_rows_below_minimum(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-r", "0", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_horizontal_all_operators_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "mul", "div", "mix",
        "-r", "3", "-c", "3", "-p", "1", "-ww", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")
    assert (tmp_path / "result.csv").exists()


def test_cli_ope_no_longer_reads_a_value_as_digit_count(run_tex_cli, tmp_path):
    # Regression test (issue #230): -a/--a-value used to be silently
    # reinterpreted as a digit-count shorthand for 'ope' and would crash with
    # an unhandled IndexError for a value outside set_min_max_value()'s 1-5
    # range (e.g. 99). 'ope' no longer reads -a/--a-value at all -- only
    # --a-digits/--a-min/--a-max affect the range now -- so a value that
    # would have crashed the old digit-count conversion must simply be
    # ignored and succeed.
    result = run_tex_cli("A4", "ope", "-o", "add", "--a-value", "99", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_a_digits_sets_the_range(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--a-digits", "3", "--b-digits", "1",
        "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert lines, "expected at least one CSV row"
    for line in lines:
        _page_number, _index, a, _operator, b, _c, _remainder = line.split(",")
        assert 100 <= int(a) <= 999
        assert 1 <= int(b) <= 9


def test_cli_com_ignores_unrelated_a_digits_flag(run_tex_cli, tmp_path):
    # 'com' reads -a/--a-value directly (the complement target); --a-digits
    # is only meaningful for nuts_calc_tex.DIGIT_COUNT_SHORTHAND_COMMANDS and
    # is simply never read here, same as --a-min/--a-max already being
    # unread by 'com' today (issue #230 -- extra params are ignored, not
    # rejected).
    result = run_tex_cli(
        "A4", "com", "-a", "100", "--a-digits", "3", "-r", "3", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize(
    ("carry_flag", "range_args", "expected_carry"),
    [
        ("--carry-borrow", ("--a-min", "1", "--a-max", "4", "--b-min", "1", "--b-max", "4"), True),
        ("--no-carry-borrow", ("--a-min", "9", "--a-max", "9", "--b-min", "9", "--b-max", "9"), False),
    ],
)
def test_cli_ope_add_carry_flags_override_impossible_ranges(
        run_tex_cli, tmp_path, carry_flag, range_args, expected_carry,
    ):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", carry_flag, *range_args,
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, result_value, _ = row.split(",")
        assert operator == "add"
        assert addition_has_carry(int(a), int(b)) is expected_carry
        assert int(result_value) == int(a) + int(b)


def test_cli_ope_add_rejects_combining_carry_flags(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--carry-borrow", "--no-carry-borrow",
        "--out-file", "result.pdf",
    )

    assert result.returncode == 2
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize(
    ("carry_flag", "expected_borrow"),
    [("--carry-borrow", True), ("--no-carry-borrow", False)],
)
def test_cli_ope_sub_carry_flags_control_borrowing(
        run_tex_cli, tmp_path, carry_flag, expected_borrow,
    ):
    result = run_tex_cli(
        "A4", "ope", "-o", "sub", carry_flag,
        "--a-min", "1", "--a-max", "9", "--b-min", "1", "--b-max", "9",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, result_value, _ = row.split(",")
        assert operator == "sub"
        assert subtraction_has_borrow(int(a), int(b)) is expected_borrow
        if expected_borrow:
            assert 10 <= int(a) <= 19
            assert 1 <= int(b) <= 9
        assert int(result_value) == int(a) - int(b) > 0


def test_cli_ope_sub_carry_borrow_respects_configured_multi_digit_range(run_tex_cli, tmp_path):
    # issue #92: a 2-digit configured range must produce a 2-digit borrowing
    # minuend, not the grade-1-only 10-19 band.
    result = run_tex_cli(
        "A4", "ope", "-o", "sub", "--carry-borrow",
        "--a-min", "10", "--a-max", "99", "--b-min", "1", "--b-max", "9",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, result_value, _ = row.split(",")
        assert operator == "sub"
        assert subtraction_has_borrow(int(a), int(b))
        assert 10 <= int(a) <= 99
        assert 1 <= int(b) <= 9
        assert int(result_value) == int(a) - int(b) > 0


def test_cli_ope_mixed_carry_accepts_add_sub(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "--mixed-carry-borrow",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("invalid_args", [("-o", "mul", "--carry-borrow"), ("-o", "add", "--mixed-carry-borrow")])
def test_cli_ope_carry_modes_reject_invalid_operators(run_tex_cli, tmp_path, invalid_args):
    result = run_tex_cli("A4", "ope", *invalid_args, "--out-file", "result.pdf")

    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize("operator", ["add", "sub"])
def test_cli_ope_operand_multiple_generates_carry_free_tens_pdf(run_tex_cli, tmp_path, operator):
    # issue #331: --a-multiple/--b-multiple restrict both operands to 何十
    # (multiples of 10); with --no-carry-borrow the tens digits never carry
    # or borrow either.
    result = run_tex_cli(
        "A4", "ope", "-o", operator,
        "--a-min", "10", "--a-max", "90", "--b-min", "10", "--b-max", "90",
        "--a-multiple", "10", "--b-multiple", "10", "--no-carry-borrow",
        "--result-max", "100",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, row_operator, b, result_value, _ = row.split(",")
        assert row_operator == operator
        assert int(a) % 10 == 0 and int(b) % 10 == 0
        assert int(result_value) <= 100
        if operator == "add":
            assert not addition_has_carry(int(a), int(b))
            assert int(result_value) == int(a) + int(b)
        else:
            assert not subtraction_has_borrow(int(a), int(b))
            assert int(result_value) == int(a) - int(b) > 0


@pytest.mark.parametrize(
    "invalid_args",
    [
        ("-o", "mul", "--a-multiple", "10"),
        ("-o", "div", "--b-multiple", "10"),
        ("--use-parentheses", "--a-multiple", "10"),
        ("--missing-value", "--a-multiple", "10"),
        ("-o", "add", "--a-multiple", "1"),
        ("-o", "add", "--a-min", "1", "--a-max", "9", "--a-multiple", "10"),
    ],
)
def test_cli_ope_operand_multiple_rejects_invalid_combinations(run_tex_cli, tmp_path, invalid_args):
    result = run_tex_cli("A4", "ope", *invalid_args, "--out-file", "result.pdf")

    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize(
    ("carry_flag", "range_args", "expected_carry"),
    [
        ("--carry-borrow", ("--a-min", "1", "--a-max", "4", "--b-min", "1", "--b-max", "4"), True),
        ("--no-carry-borrow", ("--a-min", "9", "--a-max", "9", "--b-min", "9", "--b-max", "9"), False),
    ],
)
def test_cli_ope_add_carry_flags_work_with_decimal_places(
        run_tex_cli, tmp_path, carry_flag, range_args, expected_carry,
    ):
    # issue #113: --carry-borrow/--no-carry-borrow determine carrying from
    # the raw scaled integers, so this mirrors
    # test_cli_ope_add_carry_flags_override_impossible_ranges above with
    # --a-decimal-places/--b-decimal-places added.
    result = run_tex_cli(
        "A4", "ope", "-o", "add", carry_flag, *range_args,
        "--a-decimal-places", "1", "--b-decimal-places", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, result_value, _ = row.split(",")
        assert operator == "add"
        raw_a, raw_b = round(float(a) * 10), round(float(b) * 10)
        assert addition_has_carry(raw_a, raw_b) is expected_carry
        assert float(result_value) == round(float(a) + float(b), 1)


def test_cli_ope_sub_carry_borrow_works_with_decimal_places(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "sub", "--carry-borrow",
        "--a-min", "10", "--a-max", "99", "--b-min", "1", "--b-max", "9",
        "--a-decimal-places", "1", "--b-decimal-places", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, result_value, _ = row.split(",")
        assert operator == "sub"
        raw_a, raw_b = round(float(a) * 10), round(float(b) * 10)
        assert subtraction_has_borrow(raw_a, raw_b)
        assert float(result_value) == round(float(a) - float(b), 1) > 0


def test_cli_ope_mixed_carry_borrow_works_with_decimal_places(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "--mixed-carry-borrow",
        "--a-decimal-places", "1", "--b-decimal-places", "1",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("legacy_flag", ["--carry", "--no-carry", "--mixed-carry"])
def test_cli_ope_rejects_legacy_carry_flags(run_tex_cli, tmp_path, legacy_flag):
    result = run_tex_cli("A4", "ope", legacy_flag, "--out-file", "result.pdf")

    assert result.returncode == 2
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_div_remainder_flag_forces_nonzero_remainder(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--remainder",
        "--a-min", "10", "--a-max", "99", "--b-min", "2", "--b-max", "9",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, c, remainder = row.split(",")
        assert operator == "div"
        assert int(remainder) != 0
        assert int(remainder) == int(a) - int(b) * int(c)


def test_cli_ope_div_no_remainder_flag_matches_default(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--no-remainder",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, c, remainder = row.split(",")
        assert operator == "div"
        assert remainder == "0"
        assert int(a) % int(b) == 0


def test_cli_ope_mixed_remainder_covers_both_conditions(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--mixed-remainder",
        "--a-min", "10", "--a-max", "99", "--b-min", "2", "--b-max", "9",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    remainders = {
        row.split(",")[6] == "0"
        for row in (tmp_path / "result.csv").read_text().strip().splitlines()
    }
    assert remainders == {True, False}


@pytest.mark.parametrize(
    "invalid_args",
    [
        ("-o", "add", "--remainder"),
        ("-o", "div", "mul", "--remainder"),
        ("-o", "div", "--remainder", "--use-parentheses"),
    ],
)
def test_cli_ope_remainder_modes_reject_invalid_combinations(run_tex_cli, tmp_path, invalid_args):
    result = run_tex_cli("A4", "ope", *invalid_args, "--out-file", "result.pdf")

    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_rejects_combining_remainder_flags(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--remainder", "--no-remainder",
        "--out-file", "result.pdf",
    )

    assert result.returncode == 2
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_vertical_add_sub_mul_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "mul", "--vertical",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_vertical_multi_digit_multiplier_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "3", "--b-digits", "2", "--vertical",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_vertical_div_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "3", "--b-digits", "2", "--vertical",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_vertical_mix_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mix", "--a-min", "100", "--a-max", "999",
        "--b-min", "10", "--b-max", "99", "--vertical",
        "-r", "3", "-c", "3", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_vertical_default_rows_does_not_drop_content(run_tex_cli, tmp_path):
    # Regression test: a plain (non-page-breaking) LaTeX tabular spanning
    # the whole page would get pushed as one unbreakable block once its
    # rows no longer fit a single page, leaving page 1 blank and
    # overflowing page 2 instead of flowing row by row (see
    # docs/L3_implementation/nuts_calc_tex.py.md).
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "3", "--b-digits", "2", "--vertical",
        "--out-file", "result.pdf",  # default -r 10 -c 2
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.skipif(shutil.which("pdfinfo") is None, reason="pdfinfo is required to inspect PDF page counts")
@pytest.mark.parametrize(
    ("paper_size", "expected_rows"),
    [("A3", 4), ("A4", 4), ("B5", 2), ("a4l", 2)],
)
def test_cli_ope_vertical_default_rows_match_requested_page_count(
    run_tex_cli, tmp_path, paper_size, expected_rows,
):
    result = run_tex_cli(
        paper_size, "ope", "-o", "mul", "--a-digits", "3", "--b-digits", "2",
        "--vertical", "-p", "2", "--csv", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    assert _pdf_page_count(tmp_path / "result.pdf") == 2
    assert _pdf_page_count(tmp_path / "result_read.pdf") == 2
    assert len((tmp_path / "result.csv").read_text().strip().splitlines()) == expected_rows * 2 * 2


def test_cli_ope_intermediate_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "1", "--intermediate",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_intermediate_rejects_vertical_combo(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-o", "mul", "--intermediate", "--vertical", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_intermediate_rejects_non_mul_operator(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-o", "add", "--intermediate", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_intermediate_rejects_multi_digit_b(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-o", "mul", "--intermediate", "--b-max", "15", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_use_parentheses_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--use-parentheses",
        "--a-digits", "1", "--b-digits", "1",
        "-r", "2", "-c", "2", "-ww", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_use_parentheses_mix_produces_pdfs(run_tex_cli, tmp_path):
    # -o mix (and a single non-mix operator, below) are no longer rejected:
    # op_left/op_right and the parenthesized side are chosen per problem, so
    # even a one-element --operator still varies via --use-parentheses's own
    # position randomization.
    result = run_tex_cli(
        "A4", "ope", "-o", "mix", "--use-parentheses",
        "--a-digits", "1", "--b-digits", "1",
        "-r", "3", "-c", "3", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_use_parentheses_single_operator_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--use-parentheses",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_use_parentheses_rejects_vertical_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--use-parentheses", "--vertical", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_use_parentheses_rejects_intermediate_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--intermediate", "--use-parentheses", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_use_parentheses_rejects_non_ope_command(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "2", "--use-parentheses", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_use_parentheses_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "sub", "mul", "--use-parentheses",
        "--a-digits", "2", "--b-digits", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        page_number, index, terms, structure, result_value = line.split(",")
        assert terms == "3"
        # N=3 has exactly one non-root internal node, so exactly one
        # parenthesized group appears in the self-describing structure text.
        assert structure.count("(") == 1
        assert structure.count(")") == 1
        assert result_value.lstrip("-").isdigit()
    page_number, index, terms, structure, result_value = lines[0].split(",")
    assert (page_number, index) == ("1", "1")


def test_cli_ope_use_parentheses_terms_five_produces_deeper_trees(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--use-parentheses", "--terms", "5",
        "--a-digits", "1", "--b-digits", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        page_number, index, terms, structure, result_value = line.split(",")
        assert terms == "5"
        # N=5 has 4 internal nodes, 3 of which are non-root (parenthesized).
        assert structure.count("(") == 3


def test_cli_ope_terms_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms", "4",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_terms_min_max_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms-min", "3", "--terms-max", "6",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_mixed_operators_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--terms", "4", "--mixed-operators",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_mixed_operators_with_use_parentheses_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--terms", "5", "--use-parentheses", "--mixed-operators",
        "--a-digits", "1", "--b-digits", "1",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_terms_below_floor_clamps_instead_of_failing(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms", "1",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_terms_below_floor_with_use_parentheses_clamps_to_three(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms", "2", "--use-parentheses",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    for line in lines:
        _page_number, _index, terms, _structure, _result_value = line.split(",")
        assert terms == "3"


def test_cli_ope_terms_min_greater_than_max_rejected(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms-min", "6", "--terms-max", "3", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_terms_rejects_vertical_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--terms", "4", "--vertical", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_terms_rejects_intermediate_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--intermediate", "--terms", "4", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_terms_rejects_missing_value_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--missing-value", "--terms", "4", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_terms_rejects_non_ope_command(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "2", "--terms", "4", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_multi_term_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--terms", "4", "--mixed-operators",
        "--a-digits", "1", "--b-digits", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        page_number, index, terms, mixed, expression, result_value = line.split(",")
        assert terms == "4"
        assert mixed == "True"
        tokens = expression.split(" ")
        operands = [int(token) for token in tokens[0::2]]
        operators = tokens[1::2]
        assert evaluate_mixed_expression(operands, operators) == int(result_value)


def test_cli_ope_missing_value_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--missing-value",
        "-r", "2", "-c", "2", "-ww", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_missing_value_mix_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mix", "--missing-value",
        "-r", "3", "-c", "3", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_missing_value_rejects_vertical_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--missing-value", "--vertical", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_missing_value_rejects_intermediate_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--intermediate", "--missing-value", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_missing_value_rejects_use_parentheses_combo(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "mul", "--missing-value", "--use-parentheses", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_missing_value_rejects_non_ope_command(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "2", "--missing-value", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_missing_value_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "sub", "mul", "--missing-value",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    calc_fn = {"sub": lambda a, b: a - b, "mul": lambda a, b: a * b}

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        page_number, index, a, operator, b, c, blank = line.split(",")
        assert operator in calc_fn
        assert calc_fn[operator](int(a), int(b)) == int(c)
        assert blank in ("a", "b")


def test_cli_ope_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-o", "add", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    page_number, index, a, operator, b, c, remainder = lines[0].split(",")
    assert (page_number, index, operator) == ("1", "1", "add")
    assert int(a) + int(b) == int(c)
    assert remainder == "0"


def test_cli_com_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "com", "-a", "100", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_com_requires_a_value(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "com", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_com_rejects_target_below_two(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "com", "-a", "1", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_com_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "com", "-a", "100", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_com_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "com", "-a", "100", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    page_number, index, a, target, c = lines[0].split(",")
    assert (page_number, index, target) == ("1", "1", "100")
    assert int(a) + int(c) == int(target)


def test_cli_hundred_square_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "100", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_hundred_square_with_digit_options_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "100", "--a-digits", "2", "--b-digits", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_hundred_square_multi_page_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "100", "-p", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_hundred_square_rejects_digit_above_three(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "100", "--a-digits", "4", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize("digit_value", ["6", "0", "-1"])
def test_cli_hundred_square_rejects_out_of_range_digit_cleanly(run_tex_cli, tmp_path, digit_value):
    # Regression test: digit values that fall outside set_min_max_value()'s
    # supported 1-5 range (>5 raises IndexError; <=0 silently wraps to the
    # wrong range via negative indexing) must be rejected with a clean CLI
    # error before that conversion runs, not an unhandled traceback.
    result = run_tex_cli("A4", "100", "--a-digits", digit_value, "--out-file", "result.pdf")
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "result.pdf").exists()


def test_cli_hundred_square_csv_rows_contain_real_answer_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "100", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 11  # 1 header row + 10 data rows

    header = lines[0].split(",")
    assert header[0] == "1"
    assert header[1] == ""
    top_values = [int(v) for v in header[2:]]

    first_data_row = lines[1].split(",")
    left_value = int(first_data_row[1])
    answers = [int(v) for v in first_data_row[2:]]
    assert answers == [left_value + top for top in top_values]


def test_cli_kuku_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "3", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_kuku_requires_a_value(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_kuku_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "3", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_kuku_descend_reverse_shuffle_produce_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "99", "-a", "3", "-r", "3", "-c", "2",
        "--descend", "--reverse", "--shuffle", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_kuku_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "99", "-a", "3", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, b, c = lines[0].split(",")
    assert (page_number, index, a) == ("1", "1", "3")
    assert int(a) * int(b) == int(c)


def test_cli_abc_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "aBc", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_abc_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "aBc", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_abc_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "aBc", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, b, c, d, answer = lines[0].split(",")
    assert (page_number, index) == ("1", "1")
    assert int(answer) == (int(a) * 10 + int(b)) * 10 + (int(c) * 10 + int(d))


def test_cli_squ_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "squ", "-a", "3", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_squ_requires_a_value(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "squ", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_squ_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "squ", "-a", "3", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_squ_descend_reverse_shuffle_produce_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "squ", "-a", "3", "-r", "3", "-c", "2",
        "--descend", "--reverse", "--shuffle", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_squ_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "squ", "-a", "3", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, c = lines[0].split(",")
    assert (page_number, index, a) == ("1", "1", "3")
    assert int(a) * int(a) == int(c)


def test_cli_pi_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "pi", "-a", "3", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_pi_requires_a_value(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "pi", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_pi_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "pi", "-a", "3", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_pi_descend_reverse_shuffle_produce_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "pi", "-a", "3", "-r", "3", "-c", "2",
        "--descend", "--reverse", "--shuffle", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_pi_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "pi", "-a", "3", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, c = lines[0].split(",")
    assert (page_number, index, a) == ("1", "1", "3")
    assert round(int(a) * 3.14, 2) == float(c)


def test_cli_evenodd_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "evenodd", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_evenodd_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "evenodd", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_evenodd_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "evenodd", "--a-min", "1", "--a-max", "9", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, label = lines[0].split(",")
    assert (page_number, index) == ("1", "1")
    assert 1 <= int(a) <= 9
    assert label == ("even" if int(a) % 2 == 0 else "odd")


def test_cli_multiples_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "multiples", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_multiples_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "multiples", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_multiples_count_controls_list_length(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "multiples", "--a-min", "6", "--a-max", "6", "--multiples-count", "3",
        "-r", "1", "-c", "1", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    page_number, index, a, multiples = csv_path.read_text().strip().split(",")
    assert (page_number, index, a) == ("1", "1", "6")
    assert multiples == "6 12 18"


def test_cli_multiples_count_rejected_for_other_commands(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "squ", "-a", "3", "--multiples-count", "3", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_divisors_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "divisors", "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_divisors_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "divisors", "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_divisors_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "divisors", "--a-min", "12", "--a-max", "12",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4  # rows * columns
    page_number, index, a, divisors = lines[0].split(",")
    assert (page_number, index, a) == ("1", "1", "12")
    assert divisors == "1 2 3 4 6 12"


def test_cli_divisors_rejects_a_min_below_one(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "divisors", "--a-min", "0", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_frac_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "--numerator-digits", "1", "--denominator-digits", "1",
        "--same-denominator", "--proper-operands", "--proper-result",
        "-o", "add", "sub", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_frac_csv_rows_contain_exact_fraction_data(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "--numerator-digits", "1", "--denominator-digits", "1",
        "-o", "mul", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    assert len(lines[0].split(",")) == 11
    for row in lines:
        assert row.split(",")[-2:] == ["0", "0"]  # a_whole/b_whole (#112): unused without --a/b-fraction-form


def test_cli_frac_mixed_number_form_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "add",
        "--numerator-digits", "1", "--denominator-digits", "1", "--same-denominator",
        "--a-fraction-form", "mixed", "--b-fraction-form", "mixed",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for row in lines:
        a_whole, b_whole = row.split(",")[-2:]
        assert 1 <= int(a_whole) <= 9
        assert 1 <= int(b_whole) <= 9


def test_cli_frac_mixed_number_form_mix_expands_to_proper_or_mixed(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "sub",
        "--numerator-digits", "1", "--denominator-digits", "1", "--same-denominator", "--proper-result",
        "--a-fraction-form", "mix", "--b-fraction-form", "mix",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 25
    a_wholes = {int(row.split(",")[-2]) for row in lines}
    b_wholes = {int(row.split(",")[-1]) for row in lines}
    assert a_wholes & {0} and a_wholes - {0}  # both proper (0) and mixed (>0) forms appeared
    assert b_wholes & {0} and b_wholes - {0}


def test_cli_frac_fraction_form_rejects_improper(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "add", "--a-fraction-form", "improper", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_frac_fraction_form_rejects_mix_operator(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "mix", "--a-fraction-form", "mixed", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_frac_fraction_form_rejects_multiple_operators(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "add", "sub", "--a-fraction-form", "mixed", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_fraction_form_rejects_non_compare_non_frac_command(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "--a-fraction-form", "mixed", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_add_sub_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "2", "--b-decimal-places", "2",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        fields = row.split(",")
        assert "." in fields[2] and "." in fields[4] and "." in fields[5]


def test_cli_ope_decimal_multiply_by_integer_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_decimal_divide_by_decimal_produces_whole_number_answers(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "1", "--b-decimal-places", "1",
        "-r", "3", "-c", "3", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        answer = row.split(",")[5]
        assert "." not in answer  # a/b decimal places are equal -> exact integer quotient


def test_cli_ope_integer_dividend_produces_whole_dividend_and_quotient(run_tex_cli, tmp_path):
    # grade-5 "整数と小数の割り算" 整数÷小数 option (issue #317): the dividend is
    # a whole number, the divisor is a decimal, and the quotient is exact.
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "0", "--b-decimal-places", "1", "--integer-dividend",
        "-r", "3", "-c", "3", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, dividend, _, divisor, quotient, remainder = row.split(",")
        assert "." not in dividend      # whole-number dividend
        assert "." in divisor           # decimal divisor
        assert "." not in quotient      # exact whole-number quotient
        assert remainder == "0"


def test_cli_ope_mixed_dividend_produces_both_whole_and_decimal_dividends(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "1", "--b-decimal-places", "1", "--mixed-dividend",
        "-r", "5", "-c", "4", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    dividends = [row.split(",")[2] for row in (tmp_path / "result.csv").read_text().strip().splitlines()]
    assert any("." in value for value in dividends)      # decimal dividends
    assert any("." not in value for value in dividends)  # whole-number dividends


@pytest.mark.parametrize(
    "extra_args",
    [
        ["-o", "mul"],                                          # not div
        ["-o", "div", "--b-decimal-places", "0"],               # divisor is not a decimal
        ["-o", "div", "--b-decimal-places", "1", "--mixed-remainder"],  # conflicts with --remainder family
        ["-o", "div", "--b-decimal-places", "1", "--use-parentheses"],
    ],
)
def test_cli_ope_integer_dividend_rejects_unsupported_combinations(run_tex_cli, tmp_path, extra_args):
    result = run_tex_cli(
        "A4", "ope", "--a-digits", "2", "--b-digits", "2", "--integer-dividend",
        *extra_args, "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_add_sub_mul_vertical_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "sub", "mul", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "2", "--b-decimal-places", "2",
        "--vertical", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_decimal_multiply_by_integer_vertical_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "--vertical", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_decimal_divide_by_integer_vertical_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "--vertical", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_decimal_multiply_by_decimal_vertical_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "2",
        "--a-decimal-places", "1", "--b-decimal-places", "1",
        "--vertical", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_decimal_rejects_vertical_with_decimal_divisor(run_tex_cli, tmp_path):
    # g5-decimal-div (decimal-by-decimal division): `longdivision`'s
    # `\intlongdivision` requires an integer divisor. Split out to a
    # separate agenda issue rather than silently shifting the divisor's
    # decimal point (which would show a different expression than the
    # horizontal form) -- see nuts_calc_tex.py.md.
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-decimal-places", "1", "--b-decimal-places", "1",
        "--vertical", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_rejects_mismatched_places_with_add(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "add", "--a-decimal-places", "2", "--b-decimal-places", "1",
        "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_rejects_dividend_places_below_divisor_places(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-decimal-places", "1", "--b-decimal-places", "2",
        "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_rejects_non_ope_command(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "com", "-a", "10", "--a-decimal-places", "1", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_decimal_mixed_operand_order_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "--mixed-decimal-operand-order",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_ope_decimal_mixed_operand_order_vertical_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "--mixed-decimal-operand-order", "--vertical",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_mixed_operand_order_rejects_non_mul_operator(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-digits", "2", "--b-digits", "1",
        "--a-decimal-places", "1", "--mixed-decimal-operand-order",
        "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_mixed_operand_order_rejects_equal_decimal_places(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-decimal-places", "1", "--b-decimal-places", "1",
        "--mixed-decimal-operand-order", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_ope_mixed_operand_order_rejects_non_ope_command(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "--mixed-decimal-operand-order", "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_mixed_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "-o", "mix", "--numerator-digits", "1", "--denominator-digits", "1",
        "--decimal-places", "1", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_mixed_multi_term_mixed_operators_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "-o", "mix", "--terms", "3", "--mixed-operators",
        "--numerator-digits", "1", "--denominator-digits", "1", "--decimal-places", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for row in lines:
        fields = row.split(",")
        assert fields[2] == "3"  # terms
        assert fields[3] == "True"  # mixed


def test_cli_mixed_csv_rows_contain_exact_fraction_result(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "-o", "div", "--numerator-digits", "1", "--denominator-digits", "1",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    assert len(lines[0].split(",")) == 7


def test_cli_mixed_rejects_decimal_places_out_of_range(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "mixed", "--decimal-places", "9", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_mixed_kind_options_rejected_on_non_mixed_command(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "frac", "--a-kind", "int", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_compare_accepts_kind_options(run_tex_cli, tmp_path):
    """issue #171: 'compare' accepts --a-kind/--b-kind/--decimal-places,
    unlike other non-'mixed' commands (see the rejection test above)."""
    result = run_tex_cli(
        "A4", "compare", "--a-kind", "int", "decimal", "fraction",
        "--b-kind", "int", "decimal", "fraction", "--decimal-places", "1",
        "-r", "3", "-c", "3", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 9


def test_cli_compare_defaults_to_fraction_vs_fraction(run_tex_cli, tmp_path):
    """Backward compatibility: omitting --a-kind/--b-kind still compares
    fraction vs fraction, matching pre-#171 behavior."""
    result = run_tex_cli("A4", "compare", "-r", "2", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_compare_comparison_pattern_requires_fraction_kinds(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "compare", "--a-kind", "int", "--comparison-pattern", "same-denominator",
        "--out-file", "result.pdf",
    )
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_compare_rejects_decimal_places_out_of_range(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "compare", "--decimal-places", "9", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def _raw_gcd_frac_row(a_num, a_den, operator, b_num, b_den):
    if operator == "mul":
        raw_numerator, raw_denominator = a_num * b_num, a_den * b_den
    else:
        raw_numerator, raw_denominator = a_num * b_den, a_den * b_num
    return math.gcd(raw_numerator, raw_denominator)


@pytest.mark.parametrize(
    ("reducible_flag", "operator", "check"),
    [
        ("--require-reducible", "mul", lambda gcd: gcd > 1),
        ("--require-reducible", "div", lambda gcd: gcd > 1),
        ("--no-reducible", "mul", lambda gcd: gcd == 1),
        ("--no-reducible", "div", lambda gcd: gcd == 1),
    ],
)
def test_cli_frac_reducible_flags_control_raw_gcd(run_tex_cli, tmp_path, reducible_flag, operator, check):
    result = run_tex_cli(
        "A4", "frac", "-o", operator, reducible_flag,
        "--numerator-digits", "1", "--denominator-digits", "1", "--proper-operands",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 25
    for row in lines:
        _, _, a_num, a_den, op, b_num, b_den, *_ = row.split(",")
        assert op == operator
        gcd = _raw_gcd_frac_row(int(a_num), int(a_den), op, int(b_num), int(b_den))
        assert check(gcd)


def test_cli_frac_mixed_reducible_covers_both_outcomes(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "mul", "--mixed-reducible",
        "--numerator-digits", "1", "--denominator-digits", "1", "--proper-operands",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    outcomes = {
        _raw_gcd_frac_row(int(a_num), int(a_den), op, int(b_num), int(b_den)) > 1
        for _, _, a_num, a_den, op, b_num, b_den, *_ in (
            row.split(",") for row in (tmp_path / "result.csv").read_text().strip().splitlines()
        )
    }
    assert outcomes == {True, False}


@pytest.mark.parametrize(
    "invalid_args",
    [
        ("ope", "-o", "mul", "--require-reducible"),
        ("frac", "-o", "add", "--require-reducible"),
        ("frac", "-o", "mix", "--require-reducible"),
        ("mixed", "-o", "mul", "--require-reducible"),
        ("mixed", "-o", "mul", "--a-kind", "fraction", "--b-kind", "int", "--terms", "3", "--require-reducible"),
        ("mixed", "-o", "mul", "--a-kind", "fraction", "--b-kind", "fraction", "--require-reducible"),
    ],
)
def test_cli_reducible_modes_reject_invalid_combinations(run_tex_cli, tmp_path, invalid_args):
    result = run_tex_cli("A4", *invalid_args, "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_reducible_rejects_combining_flags(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "frac", "-o", "mul", "--require-reducible", "--no-reducible",
        "--out-file", "result.pdf",
    )
    assert result.returncode == 2
    assert not (tmp_path / "result.pdf").exists()


def _parse_mixed_operand_display(display):
    match = re.fullmatch(r"\\frac\{(\d+)\}\{(\d+)\}", display)
    if match:
        return int(match.group(1)), int(match.group(2))
    return int(display), 1


@pytest.mark.parametrize(
    ("reducible_flag", "operator", "check"),
    [
        ("--require-reducible", "mul", lambda gcd: gcd > 1),
        ("--require-reducible", "div", lambda gcd: gcd > 1),
        ("--no-reducible", "mul", lambda gcd: gcd == 1),
        ("--no-reducible", "div", lambda gcd: gcd == 1),
    ],
)
def test_cli_mixed_reducible_flags_control_raw_gcd(run_tex_cli, tmp_path, reducible_flag, operator, check):
    result = run_tex_cli(
        "A4", "mixed", "-o", operator, reducible_flag,
        "--a-kind", "fraction", "--b-kind", "int",
        "--numerator-digits", "1", "--denominator-digits", "1",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 25
    for row in lines:
        _, _, _, _, expression, *_ = row.split(",")
        a_display, op, b_display = expression.split(" ")
        assert op == operator
        a_num, a_den = _parse_mixed_operand_display(a_display)
        b_num, b_den = _parse_mixed_operand_display(b_display)
        gcd = _raw_gcd_frac_row(a_num, a_den, op, b_num, b_den)
        assert check(gcd)


def test_cli_mixed_mixed_reducible_covers_both_outcomes(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "mixed", "-o", "mul", "--mixed-reducible",
        "--a-kind", "fraction", "--b-kind", "int",
        "--numerator-digits", "1", "--denominator-digits", "1",
        "-r", "5", "-c", "5", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    outcomes = set()
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, _, _, expression, *_ = row.split(",")
        a_display, op, b_display = expression.split(" ")
        a_num, a_den = _parse_mixed_operand_display(a_display)
        b_num, b_den = _parse_mixed_operand_display(b_display)
        outcomes.add(_raw_gcd_frac_row(a_num, a_den, op, b_num, b_den) > 1)
    assert outcomes == {True, False}


@pytest.mark.parametrize("command,check", [
    ("lcm", lambda a, b, c: math.lcm(a, b) == c),
    ("gcd", lambda a, b, c: math.gcd(a, b) == c),
])
def test_cli_number_pair_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path, command, check):
    result = run_tex_cli("A4", command, "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.parametrize("command", ["lcm", "gcd"])
def test_cli_number_pair_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path, command):
    result = run_tex_cli("A4", command, "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("command", ["lcm", "gcd"])
def test_cli_number_pair_digit_options_produce_pdf(run_tex_cli, tmp_path, command):
    result = run_tex_cli("A4", command, "--a-digits", "2", "--b-digits", "2", "-r", "2", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("command,check", [
    ("lcm", lambda a, b, c: math.lcm(a, b) == c),
    ("gcd", lambda a, b, c: math.gcd(a, b) == c),
])
def test_cli_number_pair_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path, command, check):
    result = run_tex_cli("A4", command, "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        page_number, index, a, b, c = line.split(",")
        assert check(int(a), int(b), int(c))


@pytest.mark.parametrize("command", ["lcm", "gcd"])
def test_cli_number_pair_rejects_intermediate(run_tex_cli, tmp_path, command):
    result = run_tex_cli("A4", command, "--intermediate", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize("command", ["simplify", "commondenom", "frac2dec", "dec2frac", "divfrac"])
def test_cli_conversion_produces_blank_and_filled_pdfs(run_tex_cli, tmp_path, command):
    result = run_tex_cli("A4", command, "-r", "3", "-c", "2", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.parametrize("command", ["simplify", "commondenom", "frac2dec", "dec2frac", "divfrac"])
def test_cli_conversion_with_bottom_answer_produces_pdf(run_tex_cli, tmp_path, command):
    result = run_tex_cli("A4", command, "-r", "3", "-c", "2", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("command", ["simplify", "commondenom", "frac2dec"])
def test_cli_conversion_digit_options_produce_pdf(run_tex_cli, tmp_path, command):
    result = run_tex_cli(
        "A4", command, "--numerator-digits", "2", "--denominator-digits", "2",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_divfrac_digit_options_produce_pdf(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "divfrac", "--a-digits", "2", "--b-digits", "2", "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_divfrac_rejects_b_min_below_one(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "divfrac", "--b-min", "0", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_simplify_csv_rows_are_reducible_and_correctly_reduced(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "simplify", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        _, _, numerator, denominator, reduced_numerator, reduced_denominator = line.split(",")
        assert math.gcd(int(numerator), int(denominator)) > 1
        assert Fraction(int(numerator), int(denominator)) == Fraction(int(reduced_numerator), int(reduced_denominator))


def test_cli_commondenom_csv_rows_share_a_denominator(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "commondenom", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        parts = [int(value) for value in line.split(",")]
        _, _, a_num, a_den, b_num, b_den, a_conv_num, a_conv_den, b_conv_num, b_conv_den = parts
        assert a_conv_den == b_conv_den
        assert Fraction(a_conv_num, a_conv_den) == Fraction(a_num, a_den)
        assert Fraction(b_conv_num, b_conv_den) == Fraction(b_num, b_den)


def test_cli_frac2dec_csv_rows_match_fraction(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "frac2dec", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        _, _, numerator, denominator, decimal_str = line.split(",")
        assert Fraction(decimal_str) == Fraction(int(numerator), int(denominator))


def test_cli_dec2frac_csv_rows_match_decimal_and_are_reduced(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "dec2frac", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        _, _, decimal_str, reduced_numerator, reduced_denominator = line.split(",")
        reduced = Fraction(int(reduced_numerator), int(reduced_denominator))
        assert Fraction(decimal_str) == reduced
        assert reduced.denominator > 1


def test_cli_divfrac_csv_rows_are_not_reduced(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "divfrac", "--a-min", "2", "--a-max", "2", "--b-min", "4", "--b-max", "4",
        "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(lines) == 4
    for line in lines:
        _, _, a, b = line.split(",")
        assert (a, b) == ("2", "4")


def test_cli_fails_clearly_when_pdflatex_missing(run_tex_cli, tmp_path, monkeypatch):
    # Simulate a PATH with no pdflatex, matching the environment-detection
    # error path (rather than the argparse validation path above).
    # NUTS_CALC_TEX_ENGINE is set explicitly since pdflatex is no longer the
    # default engine (issue #186); see
    # test_cli_fails_clearly_when_lualatex_missing_by_default for the
    # default-engine equivalent of this test.
    result = subprocess.run(
        [sys.executable, str(NUTS_CALC_TEX), "A4", "ope", "--out-file", "result.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=CLI_TIMEOUT_SECONDS,
        env={"PATH": "/nonexistent", "NUTS_CALC_TEX_ENGINE": "pdflatex"},
    )
    assert result.returncode == 1
    assert "pdflatex not found" in result.stdout


def test_cli_fails_clearly_when_lualatex_missing_by_default(run_tex_cli, tmp_path, monkeypatch):
    # Same as test_cli_fails_clearly_when_pdflatex_missing above, but without
    # setting NUTS_CALC_TEX_ENGINE, exercising the default engine (lualatex,
    # issue #186)'s binary-missing error path.
    result = subprocess.run(
        [sys.executable, str(NUTS_CALC_TEX), "A4", "ope", "--out-file", "result.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=CLI_TIMEOUT_SECONDS,
        env={"PATH": "/nonexistent"},
    )
    assert result.returncode == 1
    assert "lualatex not found" in result.stdout
