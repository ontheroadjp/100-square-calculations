"""End-to-end regression tests for nuts_calc.py, run as a real subprocess.

Purpose: safety net ahead of a planned refactor of nuts_calc.py. These tests
exercise the CLI the same way a user (or web/backend/app.py) would, and check
that PDF/CSV output is actually produced -- not just that functions return
without raising.

Where nuts_calc.py has a known, currently-unfixed bug (issue #4's 9 phases,
or issue #15's output-filename derivation), tests pin the CURRENT (buggy)
behavior rather than the intended/correct one, so an unrelated refactor
doesn't silently change it without the change showing up as a failing test.
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


@pytest.mark.parametrize("operator", ["add", "sub", "mul"])
def test_cli_vertical_supported_operators_succeed(run_cli, tmp_path, operator):
    result = run_cli("A4", "ope", "--vertical", "-o", operator, "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")


@pytest.mark.parametrize("operator", ["div", "mix"])
def test_cli_vertical_rejects_unsupported_operator(run_cli, tmp_path, operator):
    result = run_cli("A4", "ope", "--vertical", "-o", operator, "--out-file", "result.pdf")
    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


def test_cli_vertical_merge_produces_single_pdf_without_read_file(run_cli, tmp_path):
    result = run_cli("A4", "ope", "--vertical", "-m", "-r", "2", "-c", "1", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    assert not (tmp_path / "result_read.pdf").exists()


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
# Known open bugs (issue #4 / issue #15): pin current behavior so an
# unrelated refactor can't silently change it.
# ---------------------------------------------------------------------------


def test_cli_ope_equal_a_min_max_outside_small_int_cache_crashes(run_cli, tmp_path):
    # issue #4 Phase 6: `ini.a_min is not ini.a_max` uses identity comparison.
    # For values outside CPython's small-int cache (-5..256) where min==max,
    # this takes the wrong branch, builds an empty range, and later crashes
    # with IndexError on random.choice([]) -- caught by failure() -> exit(-1)
    # (255 on this platform).
    result = run_cli("A4", "ope", "--a-min", "300", "--a-max", "300", "--out-file", "result.pdf")
    assert result.returncode == 255
    assert not (tmp_path / "result.pdf").exists()


def test_cli_out_file_name_derivation_pins_current_buggy_stripping(run_cli, tmp_path):
    # issue #15: OUTFILE_NAME_READ/OUTFILE_NAME_CSV are derived via
    # `ini.out_file.rstrip('.pdf')`, a character-class strip rather than a
    # suffix strip. "output_add.pdf" loses its trailing "d" (also in the
    # strip set '.','p','d','f'), producing "output_a_read.pdf"/"output_a.csv"
    # instead of the expected "output_add_read.pdf"/"output_add.csv".
    result = run_cli("A4", "ope", "-r", "2", "-c", "1", "--csv", "--out-file", "output_add.pdf")
    assert result.returncode == 0, result.stderr

    assert (tmp_path / "output_add.pdf").exists()
    assert (tmp_path / "output_a_read.pdf").exists()
    assert (tmp_path / "output_a.csv").exists()
    assert not (tmp_path / "output_add_read.pdf").exists()
    assert not (tmp_path / "output_add.csv").exists()
