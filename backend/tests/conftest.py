import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
NUTS_CALC = BACKEND_DIR / "nuts_calc.py"

CLI_TIMEOUT_SECONDS = 30


@pytest.fixture
def run_cli(tmp_path: Path):
    """Run nuts_calc.py as a subprocess, with tmp_path as the working directory
    so relative --out-file paths (and the derived _read.pdf/.csv files) land
    in an isolated, auto-cleaned directory.
    """

    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(NUTS_CALC), *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    return _run
