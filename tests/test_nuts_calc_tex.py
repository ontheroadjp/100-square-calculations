"""End-to-end regression tests for nuts_calc_tex.py (Phase 1 foundation, issue #20).

nuts_calc_tex.py has zero code dependency on nuts_calc.py, so these tests
run it as a real subprocess, independent of tests/test_nuts_calc_cli.py.
All tests are skipped when `pdflatex` is not on PATH, since this module
requires a LaTeX distribution.
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
