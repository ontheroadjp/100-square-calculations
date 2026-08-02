"""End-to-end regression tests for nuts_calc.py, run as a real subprocess.

Purpose: safety net ahead of a planned refactor of nuts_calc.py. These tests
exercise the CLI the same way a user (or web/backend/app.py) would, and check
that PDF/CSV output is actually produced -- not just that functions return
without raising.

Issue #4's 9 phases and issue #15 (output-filename derivation) have all
been fixed; the corresponding tests verify the corrected behavior.
"""

import pytest


def _assert_is_pdf(path):
    assert path.exists(), f"expected PDF at {path}"
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


# ---------------------------------------------------------------------------
# All 7 commands run end-to-end.
#
# This directly guards the "resolved" bug documented in CLAUDE.md: before the
# 100masu.py -> nuts_calc.py migration, `ini.intermediate` (undefined name)
# was referenced for every command except 'ope', so all 6 other commands
# failed with NameError. Each parametrized case here would have failed with
# a non-zero exit code under that old bug.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command,extra_args",
    [
        ("ope", []),
        ("com", ["-a", "20"]),
        ("100", []),
        ("99", ["-a", "3"]),
        ("aBc", []),
        ("squ", ["-a", "1"]),
        ("pi", ["-a", "1"]),
    ],
)
def test_cli_command_runs_end_to_end(run_cli, tmp_path, command, extra_args):
    result = run_cli("A4", command, "-r", "3", "-c", "1", "-p", "1", "--out-file", "result.pdf", *extra_args)
    assert result.returncode == 0, result.stderr

    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.parametrize("paper_size", ["A3", "A4", "B5", "a4l"])
def test_cli_runs_for_each_paper_size(run_cli, tmp_path, paper_size):
    result = run_cli(paper_size, "ope", "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_answer_key_differs_from_blank_version(run_cli, tmp_path):
    result = run_cli("A4", "ope", "-r", "3", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    blank = (tmp_path / "result.pdf").read_bytes()
    answer = (tmp_path / "result_read.pdf").read_bytes()
    assert blank != answer


def test_cli_with_bottom_answer_produces_pdf(run_cli, tmp_path):
    result = run_cli("A4", "ope", "-r", "5", "-c", "1", "-ww", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


# ---------------------------------------------------------------------------
# --vertical (written-calculation / hissan format)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_cli_vertical_supported_operators_succeed(run_cli, tmp_path, operator):
    result = run_cli("A4", "ope", "--vertical", "-o", operator, "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("operator", ["mix"])
def test_cli_vertical_rejects_unsupported_operator(run_cli, tmp_path, operator):
    result = run_cli("A4", "ope", "--vertical", "-o", operator, "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_vertical_merge_produces_single_pdf_without_read_file(run_cli, tmp_path):
    result = run_cli("A4", "ope", "--vertical", "-m", "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    assert not (tmp_path / "result_read.pdf").exists()


def test_cli_vertical_mul_supports_multi_digit_multiplier(run_cli, tmp_path):
    # 3-digit x 2-digit, matching the web frontend's `g4-mul` preset.
    result = run_cli(
        "A4", "ope", "--vertical", "-o", "mul", "-a", "3", "-b", "2",
        "-r", "2", "-c", "1", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


@pytest.mark.parametrize("a_value,b_value", [(2, 1), (3, 2)])
def test_cli_vertical_div_matches_g3_g4_preset_digit_ranges(run_cli, tmp_path, a_value, b_value):
    # (2, 1): matches the web frontend's `g3-div` preset (2-digit / 1-digit).
    # (3, 2): matches the web frontend's `g4-div` preset (3-digit / 2-digit).
    result = run_cli(
        "A4", "ope", "--vertical", "-o", "div", "-a", str(a_value), "-b", str(b_value),
        "-r", "3", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_vertical_div_blank_and_filled_pdfs_differ(run_cli, tmp_path):
    result = run_cli(
        "A4", "ope", "--vertical", "-o", "div", "-a", "3", "-b", "2",
        "-r", "3", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    blank = (tmp_path / "result.pdf").read_bytes()
    answer = (tmp_path / "result_read.pdf").read_bytes()
    assert blank != answer


# ---------------------------------------------------------------------------
# --merge for the '100' command (separate next_content logic from 'ope')
# ---------------------------------------------------------------------------


def test_cli_100_merge_produces_single_pdf_without_read_file(run_cli, tmp_path):
    result = run_cli("A4", "100", "-m", "-p", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    assert not (tmp_path / "result_read.pdf").exists()


def test_cli_ope_merge_across_multiple_pages_succeeds(run_cli, tmp_path):
    result = run_cli("A4", "ope", "-m", "-p", "2", "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    assert not (tmp_path / "result_read.pdf").exists()


# ---------------------------------------------------------------------------
# --descend / --reverse / --shuffle for 99 / squ / pi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command,extra", [("99", ["-a", "3"]), ("squ", ["-a", "1"]), ("pi", ["-a", "1"])])
@pytest.mark.parametrize("flag", ["--descend", "--reverse", "--shuffle"])
def test_cli_ordering_flags_succeed(run_cli, tmp_path, command, extra, flag):
    result = run_cli("A4", command, flag, "-r", "4", "-c", "1", "--out-file", "result.pdf", *extra)
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


# ---------------------------------------------------------------------------
# --csv row counts
# ---------------------------------------------------------------------------


def test_cli_csv_flag_writes_rows_per_column_per_page(run_cli, tmp_path):
    rows, columns, pages = 3, 2, 1
    result = run_cli(
        "A4", "ope", "-r", str(rows), "-c", str(columns), "-p", str(pages),
        "--csv", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr

    csv_lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(csv_lines) == rows * columns * pages


def test_cli_100_csv_flag_writes_eleven_rows_per_page(run_cli, tmp_path):
    pages = 2
    result = run_cli("A4", "100", "-p", str(pages), "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    assert len(csv_lines) == 11 * pages


# ---------------------------------------------------------------------------
# Fixed bugs (issue #4): verify the corrected behavior via the CSV data
# actually generated, not just a successful exit code.
# ---------------------------------------------------------------------------


def test_cli_ope_add_default_range_can_reach_upper_bound(run_cli, tmp_path):
    # issue #4 Phase 2 (fixed): range(ini.a_min, ini.a_max) used to exclude
    # a_max, so the default a-range's upper bound (9) could never appear.
    # Statistical check: with 200 independent draws from {1..9}, the chance
    # 9 never appears if the range were still exclusive of a differently
    # sized set is negligible; if the fix regresses, this reliably fails.
    result = run_cli("A4", "ope", "-o", "add", "-r", "200", "-c", "1", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    a_values = {int(line.split(",")[3]) for line in csv_lines}
    assert a_values == set(range(1, 10))


def test_cli_com_seed_can_reach_target_minus_one(run_cli, tmp_path):
    # issue #4 Phase 8 (fixed): range(1, target - 1) used to exclude
    # a = target - 1 (the boundary that yields the valid answer c = 1).
    target = 5
    result = run_cli("A4", "com", "-a", str(target), "-r", "200", "-c", "1", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_lines = (tmp_path / "result.csv").read_text().strip().splitlines()
    a_values = {int(line.split(",")[3]) for line in csv_lines}
    assert (target - 1) in a_values


def test_cli_ope_unsatisfiable_sub_fails_fast_instead_of_hanging(run_cli, tmp_path):
    # issue #4 Phase 5 (fixed): calc_sub retried forever when no (a, b) pair
    # satisfies a - b > 0. a is fixed at 1, b at 5, so a - b is always -4.
    # Before the fix this would have hung until conftest's CLI_TIMEOUT_SECONDS
    # killed the subprocess; now it should fail quickly with a clear error.
    result = run_cli(
        "A4", "ope", "--a-min", "1", "--a-max", "1", "--b-min", "5", "--b-max", "5",
        "-o", "sub", "--out-file", "result.pdf",
    )
    assert result.returncode != 0
    assert not (tmp_path / "result.pdf").exists()


@pytest.mark.parametrize("flag", ["-r", "-c"])
def test_cli_rejects_zero_rows_or_columns(run_cli, tmp_path, flag):
    # issue #4 Phase 9 follow-up: -r 0 / -c 0 used to crash with
    # ZeroDivisionError (in two different spots) instead of failing with a
    # clear validation message.
    result = run_cli("A4", "ope", flag, "0", "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


# ---------------------------------------------------------------------------
# Fixed bug (issue #15): output-filename derivation.
# ---------------------------------------------------------------------------


def test_cli_ope_equal_a_min_max_outside_small_int_cache_succeeds(run_cli, tmp_path):
    # issue #4 Phase 6 (fixed): `ini.a_min is not ini.a_max` was an identity
    # comparison. For values outside CPython's small-int cache (-5..256) where
    # min==max, it used to take the wrong branch, build an empty range, and
    # crash with IndexError on random.choice([]). Now uses `!=`, so the equal
    # case correctly falls back to a single-value list regardless of int
    # identity.
    result = run_cli("A4", "ope", "--a-min", "300", "--a-max", "300", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


def test_cli_out_file_name_derivation_handles_names_ending_in_pdf_chars(run_cli, tmp_path):
    # issue #15 (fixed): OUTFILE_NAME_READ/OUTFILE_NAME_CSV used to be derived
    # via `ini.out_file.rstrip('.pdf')`, a character-class strip rather than a
    # suffix strip. "output_add.pdf" used to lose its trailing "d" (also in
    # the strip set '.','p','d','f'), producing "output_a_read.pdf"/
    # "output_a.csv" instead of "output_add_read.pdf"/"output_add.csv". Now
    # uses os.path.splitext, which only removes the actual extension.
    result = run_cli("A4", "ope", "-r", "2", "-c", "1", "--csv", "--out-file", "output_add.pdf")
    assert result.returncode == 0, result.stderr

    assert (tmp_path / "output_add.pdf").exists()
    assert (tmp_path / "output_add_read.pdf").exists()
    assert (tmp_path / "output_add.csv").exists()
    assert not (tmp_path / "output_a_read.pdf").exists()
    assert not (tmp_path / "output_a.csv").exists()
