"""Unit tests for backend/problem_generation.py's in-process, PDF-free
problem generation (issue #138).

These call `nuts_calc.py`/`nuts_calc_tex.py`'s data-generation functions
directly (no subprocess, no PDF/LaTeX byte output, no pdflatex required).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest

import problem_generation  # noqa: E402


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_returns_exactly_num_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 7, "operator": ["add"]}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 7


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
@pytest.mark.parametrize("operator", ["add", "sub", "mul", "div"])
def test_generate_problems_problem_values_are_consistent(renderer_name: str, operator: str) -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 20,
        "a_min": 10, "a_max": 99, "b_min": 1, "b_max": 9, "operator": [operator],
    }
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 20
    for problem in problems:
        assert problem["operator"] == operator
        a, b, result, remainder = problem["a"], problem["b"], problem["result"], problem["remainder"]
        if operator == "add":
            assert a + b == result
        elif operator == "sub":
            assert a - b == result
        elif operator == "mul":
            assert a * b == result
        elif operator == "div":
            assert a == b * result + remainder


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_a_value_shorthand_derives_range(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 10, "a_value": 1, "b_value": 1, "operator": ["add"]}
    problems = problem_generation.generate_problems(params, renderer_name)
    for problem in problems:
        assert 1 <= problem["a"] <= 9
        assert 1 <= problem["b"] <= 9


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_intermediate_includes_memo(renderer_name: str) -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 5,
        "a_min": 10, "a_max": 99, "b_min": 1, "b_max": 9,
        "operator": ["mul"], "intermediate": True,
    }
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 5
    for problem in problems:
        assert "intermediate_memo" in problem
        tens_digit, ones_digit = divmod(problem["a"], 10)
        assert problem["intermediate_memo"] == f"{tens_digit * problem['b']:02d}{ones_digit * problem['b']:02d}"


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_intermediate_rejects_non_mul_operator(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 1, "operator": ["add"], "intermediate": True}
    with pytest.raises(ValueError, match="intermediate only supports a single 'mul' operator"):
        problem_generation.generate_problems(params, renderer_name)


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_intermediate_rejects_multi_digit_b_max(renderer_name: str) -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 1,
        "operator": ["mul"], "b_max": 10, "intermediate": True,
    }
    with pytest.raises(ValueError, match="single-digit second operand"):
        problem_generation.generate_problems(params, renderer_name)


def test_generate_problems_rejects_unsupported_command_type() -> None:
    with pytest.raises(ValueError, match="not yet supported"):
        problem_generation.generate_problems({"paper_size": "A4", "command_type": "frac", "num": 1}, "latex")


@pytest.mark.parametrize(
    "flag", ["use_parentheses", "missing_value", "terms", "terms_min", "terms_max", "mixed_operators"]
)
def test_generate_problems_rejects_unsupported_ope_variant_flags(flag: str) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 1, flag: True}
    with pytest.raises(ValueError, match="not yet supported"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("num", [0, -1, 1.5, "5", None])
def test_generate_problems_rejects_invalid_num(num: object) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": num}
    with pytest.raises(ValueError, match="num must be a positive integer"):
        problem_generation.generate_problems(params, "reportlab")


def test_generate_problems_latex_remainder_mode_required_yields_nonzero_remainder() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 20,
        "a_min": 10, "a_max": 99, "b_min": 2, "b_max": 9,
        "operator": ["div"], "remainder_mode": "required",
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert all(problem["remainder"] != 0 for problem in problems)


def test_generate_problems_latex_decimal_places_are_recorded() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 5,
        "a_min": 10, "a_max": 99, "b_min": 1, "b_max": 9,
        "operator": ["add"], "a_decimal_places": 1, "b_decimal_places": 0,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert all(problem["a_decimal_places"] == 1 and problem["b_decimal_places"] == 0 for problem in problems)
