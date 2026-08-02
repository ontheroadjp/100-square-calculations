"""End-to-end regression tests for nuts_calc_tex.py (Phase 1 foundation #20;
`ope` command Phase 2 #21; `com` command Phase 3 #22).

nuts_calc_tex.py has zero code dependency on nuts_calc.py, so these tests
run it as a real subprocess, independent of tests/test_nuts_calc_cli.py.
All tests are skipped when `pdflatex` is not on PATH, since this module
requires a LaTeX distribution. Pure-Python `ope`/`com` generation logic
that doesn't need pdflatex is covered separately in
test_nuts_calc_tex_ope_generation.py and
test_nuts_calc_tex_com_generation.py.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NUTS_CALC_TEX = REPO_ROOT / "nuts_calc_tex.py"

CLI_TIMEOUT_SECONDS = 60

pytestmark = pytest.mark.skipif(
    shutil.which("pdflatex") is None,
    reason="nuts_calc_tex.py requires a LaTeX distribution (pdflatex) on PATH",
)


@pytest.fixture
def run_tex_cli(tmp_path: Path):
    """Run nuts_calc_tex.py as a subprocess, with tmp_path as the working
    directory so relative --out-file paths land in an isolated, auto-cleaned
    directory.
    """

    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(NUTS_CALC_TEX), *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    return _run


def _assert_is_pdf(path: Path) -> None:
    assert path.exists(), f"expected PDF at {path}"
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


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
        "A4", "ope", "-o", "mul", "--a-value", "3", "--b-value", "2", "--vertical",
        "-r", "2", "-c", "2", "--out-file", "result.pdf",
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_vertical_div_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "div", "--a-value", "3", "--b-value", "2", "--vertical",
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
        "A4", "ope", "-o", "div", "--a-value", "3", "--b-value", "2", "--vertical",
        "--out-file", "result.pdf",  # default -r 10 -c 2
    )
    assert result.returncode == 0, result.stderr
    _assert_is_pdf(tmp_path / "result.pdf")
    _assert_is_pdf(tmp_path / "result_read.pdf")


def test_cli_ope_intermediate_produces_pdfs(run_tex_cli, tmp_path):
    result = run_tex_cli(
        "A4", "ope", "-o", "mul", "--a-value", "2", "--b-value", "1", "--intermediate",
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


def test_cli_ope_csv_rows_contain_real_problem_data(run_tex_cli, tmp_path):
    result = run_tex_cli("A4", "ope", "-o", "add", "-r", "2", "-c", "2", "--csv", "--out-file", "result.pdf")
    assert result.returncode == 0, result.stderr

    csv_path = tmp_path / "result.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert len(lines) == 4
    page_number, index, a, operator, b, c = lines[0].split(",")
    assert (page_number, index, operator) == ("1", "1", "add")
    assert int(a) + int(b) == int(c)


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


def test_cli_fails_clearly_when_pdflatex_missing(run_tex_cli, tmp_path, monkeypatch):
    # Simulate a PATH with no pdflatex, matching the environment-detection
    # error path (rather than the argparse validation path above).
    result = subprocess.run(
        [sys.executable, str(NUTS_CALC_TEX), "A4", "ope", "--out-file", "result.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=CLI_TIMEOUT_SECONDS,
        env={"PATH": "/nonexistent"},
    )
    assert result.returncode == 1
    assert "pdflatex not found" in result.stdout
