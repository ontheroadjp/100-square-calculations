"""Unit tests for web/backend/renderers.py's renderer-selection and
command-building logic (issue #36).

These exercise the pure-Python functions directly (no Flask app, no
subprocess execution) so they run without a running backend or pdflatex.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "web" / "backend"))

import pytest

import renderers  # noqa: E402


def test_get_renderer_name_defaults_to_reportlab_when_unset(monkeypatch) -> None:
    monkeypatch.delenv(renderers.RENDERER_ENV_VAR, raising=False)
    assert renderers.get_renderer_name() == "reportlab"


def test_get_renderer_name_reads_env_var(monkeypatch) -> None:
    monkeypatch.setenv(renderers.RENDERER_ENV_VAR, "latex")
    assert renderers.get_renderer_name() == "latex"


def test_get_renderer_name_rejects_unknown_value(monkeypatch) -> None:
    monkeypatch.setenv(renderers.RENDERER_ENV_VAR, "bogus")
    with pytest.raises(ValueError, match="Unknown NUTS_CALC_RENDERER value"):
        renderers.get_renderer_name()


def test_build_command_selects_script_path_per_renderer() -> None:
    params = {"paper_size": "A4", "command_type": "ope"}
    reportlab_command = renderers.build_command("reportlab", params, "out.pdf")
    latex_command = renderers.build_command("latex", params, "out.pdf")

    assert reportlab_command[1] == str(renderers.RENDERER_SCRIPTS["reportlab"])
    assert latex_command[1] == str(renderers.RENDERER_SCRIPTS["latex"])
    assert reportlab_command[1].endswith("nuts_calc.py")
    assert latex_command[1].endswith("nuts_calc_tex.py")


def test_build_command_invokes_the_running_interpreter() -> None:
    # Must match sys.executable (the interpreter running this backend
    # process), not a hardcoded 'python'/'python3': a mismatched interpreter
    # could lack the renderer's dependencies (e.g. reportlab) or not exist
    # at all in the target environment.
    params = {"paper_size": "A4", "command_type": "ope"}
    command = renderers.build_command("reportlab", params, "out.pdf")
    assert command[0] == sys.executable


def test_build_command_requires_paper_size_and_command_type() -> None:
    with pytest.raises(ValueError, match="Missing required parameters"):
        renderers.build_command("reportlab", {}, "out.pdf")


def test_build_command_includes_positional_and_out_file() -> None:
    params = {"paper_size": "A4", "command_type": "squ"}
    command = renderers.build_command("reportlab", params, "out.pdf")
    assert command[2:4] == ["A4", "squ"]
    assert command[-2:] == ["--out-file", "out.pdf"]


def test_build_command_translates_optional_scalar_params() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "squ",
        "a_value": 3,
        "rows": 5,
        "columns": 2,
        "page": 2,
    }
    command = renderers.build_command("reportlab", params, "out.pdf")
    assert "--a-value" in command and command[command.index("--a-value") + 1] == "3"
    assert "--rows" in command and command[command.index("--rows") + 1] == "5"
    assert "--columns" in command and command[command.index("--columns") + 1] == "2"
    assert "--page" in command and command[command.index("--page") + 1] == "2"


def test_build_command_translates_boolean_flags() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "99",
        "descend": True,
        "reverse": True,
        "shuffle": False,
        "with_bottom_answer": True,
    }
    command = renderers.build_command("reportlab", params, "out.pdf")
    assert "--descend" in command
    assert "--reverse" in command
    assert "--shuffle" not in command
    assert "--with-bottom-answer" in command


def test_build_command_passes_operator_list_once() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "operator": ["add", "sub"],
    }
    command = renderers.build_command("reportlab", params, "out.pdf")
    idx = command.index("--operator")
    assert command[idx : idx + 3] == ["--operator", "add", "sub"]
    assert command.count("--operator") == 1


def test_build_command_translates_fraction_params() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "frac",
        "operator": ["add", "sub"],
        "numerator_digits": 1,
        "denominator_digits": 2,
        "same_denominator": True,
        "proper_operands": True,
        "proper_result": True,
    }
    command = renderers.build_command("latex", params, "out.pdf")

    assert command[command.index("--numerator-digits") + 1] == "1"
    assert command[command.index("--denominator-digits") + 1] == "2"
    assert "--same-denominator" in command
    assert "--proper-operands" in command
    assert "--proper-result" in command


def test_build_command_translates_different_denominators() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "frac",
        "different_denominators": True,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert "--different-denominators" in command


def test_build_command_translates_decimal_places() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "a_decimal_places": 2,
        "b_decimal_places": 1,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert command[command.index("--a-decimal-places") + 1] == "2"
    assert command[command.index("--b-decimal-places") + 1] == "1"


def test_build_command_translates_mixed_params() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "mixed",
        "decimal_places": 1,
        "a_kind": ["int", "decimal"],
        "b_kind": ["fraction"],
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert command[command.index("--decimal-places") + 1] == "1"
    idx = command.index("--a-kind")
    assert command[idx : idx + 3] == ["--a-kind", "int", "decimal"]
    idx = command.index("--b-kind")
    assert command[idx : idx + 2] == ["--b-kind", "fraction"]


def test_build_command_translates_missing_value() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "operator": ["add", "sub"],
        "missing_value": True,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert "--missing-value" in command


def test_build_command_omits_missing_value_when_false() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "missing_value": False,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert "--missing-value" not in command


def test_build_command_translates_terms_params() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "operator": ["mix"],
        "terms": 4,
        "mixed_operators": True,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert command[command.index("--terms") + 1] == "4"
    assert "--mixed-operators" in command


def test_build_command_translates_terms_min_max() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "terms_min": 3,
        "terms_max": 5,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert command[command.index("--terms-min") + 1] == "3"
    assert command[command.index("--terms-max") + 1] == "5"


def test_build_command_omits_mixed_operators_when_false() -> None:
    params = {
        "paper_size": "A4",
        "command_type": "ope",
        "mixed_operators": False,
    }
    command = renderers.build_command("latex", params, "out.pdf")
    assert "--mixed-operators" not in command
