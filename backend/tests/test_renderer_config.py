"""Unit tests for backend/renderer_config.py's renderer-name resolution
(issue #36; module renamed from renderers.py and reduced to renderer-name
resolution plus the shared RendererRequest type in issue #297).

These exercise the pure-Python `get_renderer_name()` directly (no Flask app,
no subprocess execution) so they run without a running backend or pdflatex.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest

import renderer_config  # noqa: E402


def test_get_renderer_name_defaults_to_latex_when_unset(monkeypatch) -> None:
    monkeypatch.delenv(renderer_config.RENDERER_ENV_VAR, raising=False)
    assert renderer_config.get_renderer_name() == "latex"


def test_get_renderer_name_reads_env_var(monkeypatch) -> None:
    monkeypatch.setenv(renderer_config.RENDERER_ENV_VAR, "latex")
    assert renderer_config.get_renderer_name() == "latex"


def test_get_renderer_name_rejects_unknown_value(monkeypatch) -> None:
    monkeypatch.setenv(renderer_config.RENDERER_ENV_VAR, "bogus")
    with pytest.raises(ValueError, match="Unknown NUTS_CALC_RENDERER value"):
        renderer_config.get_renderer_name()


def test_get_renderer_name_rejects_removed_reportlab(monkeypatch) -> None:
    # nuts_calc.py/reportlab was removed (issue #232); explicit reportlab
    # is no longer a special case, just another unknown value.
    monkeypatch.setenv(renderer_config.RENDERER_ENV_VAR, "reportlab")
    with pytest.raises(ValueError, match="Unknown NUTS_CALC_RENDERER value"):
        renderer_config.get_renderer_name()
