"""Unit tests for backend/problem_generation.py's in-process, PDF-free
problem generation (issue #138).

These call `nuts_calc.py`/`nuts_calc_tex.py`'s data-generation functions
directly (no subprocess, no PDF/LaTeX byte output, no pdflatex required).
"""

import math
import sys
from fractions import Fraction
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import pytest

import nuts_calc_tex  # noqa: E402
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
        problem_generation.generate_problems({"paper_size": "A4", "command_type": "evenodd", "num": 1}, "latex")


@pytest.mark.parametrize("flag", ["use_parentheses", "missing_value", "terms"])
def test_generate_problems_rejects_ope_variant_flags_for_reportlab(flag: str) -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 1, flag: True if flag != "terms" else 4}
    with pytest.raises(ValueError, match="not supported by the reportlab renderer"):
        problem_generation.generate_problems(params, "reportlab")


def test_generate_problems_use_parentheses_returns_tree_shaped_problems() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 10,
        "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9, "operator": ["add"], "use_parentheses": True,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 10
    for problem in problems:
        assert set(problem) == {"index", "operands", "operators", "tree", "result"}
        assert len(problem["operands"]) == 3  # default term count floor for --use-parentheses is 3
        assert len(problem["operators"]) == 2
        assert isinstance(problem["tree"], dict)
        assert set(problem["tree"]) == {"value", "operator", "left", "right"}


def test_generate_problems_use_parentheses_with_terms_range() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 5,
        "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9, "operator": ["add"],
        "use_parentheses": True, "terms_min": 4, "terms_max": 4,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert all(len(problem["operands"]) == 4 for problem in problems)


def test_generate_problems_missing_value_returns_solvable_equations() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 20,
        "a_min": 10, "a_max": 99, "b_min": 1, "b_max": 9, "operator": ["add"], "missing_value": True,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 20
    for problem in problems:
        assert set(problem) == {"index", "a", "b", "operator", "c", "blank"}
        assert problem["blank"] in ("a", "b")
        assert problem["a"] + problem["b"] == problem["c"]


def test_generate_problems_terms_family_returns_multi_term_problems() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 10,
        "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9, "operator": ["add"], "terms": 4,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 10
    for problem in problems:
        assert set(problem) == {"index", "operands", "operators", "mixed", "result"}
        assert len(problem["operands"]) == 4
        assert len(problem["operators"]) == 3
        assert problem["mixed"] is False
        total = problem["operands"][0]
        for operand in problem["operands"][1:]:
            total += operand
        assert total == problem["result"]


def test_generate_problems_terms_family_with_mixed_operators() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 10,
        "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
        "operator": ["add", "sub", "mul"], "terms_min": 3, "terms_max": 5, "mixed_operators": True,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 10
    for problem in problems:
        assert problem["mixed"] is True
        assert 3 <= len(problem["operands"]) <= 5
        expected = nuts_calc_tex.evaluate_mixed_expression(problem["operands"], problem["operators"])
        assert expected == problem["result"]


def test_generate_problems_missing_value_rejects_use_parentheses_combo() -> None:
    params = {
        "paper_size": "A4", "command_type": "ope", "num": 1,
        "missing_value": True, "use_parentheses": True,
    }
    with pytest.raises(ValueError, match="missing_value cannot be combined with use_parentheses"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_missing_value_rejects_terms_combo() -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 1, "missing_value": True, "terms": 4}
    with pytest.raises(ValueError, match="missing_value cannot be combined with the terms family"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_rejects_terms_min_greater_than_terms_max() -> None:
    params = {"paper_size": "A4", "command_type": "ope", "num": 1, "terms_min": 5, "terms_max": 3}
    with pytest.raises(ValueError, match="terms_min must be less than or equal to terms_max"):
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


def test_generate_problems_hundred_square_is_explicitly_unsupported() -> None:
    params = {"paper_size": "A4", "command_type": "100", "num": 1, "a_value": 1, "b_value": 1}
    with pytest.raises(ValueError, match="not yet supported"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_com_returns_valid_complement_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "com", "num": 10, "a_value": 10}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 10
    for problem in problems:
        assert set(problem) == {"index", "a", "target", "c"}
        assert problem["target"] == 10
        assert 1 <= problem["a"] < 10
        assert problem["a"] + problem["c"] == 10


def test_generate_problems_com_requires_a_value() -> None:
    params = {"paper_size": "A4", "command_type": "com", "num": 1}
    with pytest.raises(ValueError, match="a_value .* is required for the 'com' command"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_com_rejects_target_below_minimum() -> None:
    params = {"paper_size": "A4", "command_type": "com", "num": 1, "a_value": 1}
    with pytest.raises(ValueError, match="must be at least"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_kuku_returns_valid_times_table_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "99", "num": 9, "a_value": 7}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 9
    for problem in problems:
        assert set(problem) == {"index", "a", "b", "c"}
        assert problem["a"] == 7
        assert problem["a"] * problem["b"] == problem["c"]


def test_generate_problems_kuku_requires_a_value() -> None:
    params = {"paper_size": "A4", "command_type": "99", "num": 1}
    with pytest.raises(ValueError, match="a_value .* is required for the '99' command"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_abc_returns_valid_conversion_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "aBc", "num": 10}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 10
    for problem in problems:
        assert set(problem) == {"index", "a", "b", "c", "d"}
        for digit_key in ("a", "b", "c", "d"):
            assert 0 <= problem[digit_key] <= 9


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_squ_returns_valid_square_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "squ", "num": 5, "a_value": 3}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 5
    for problem in problems:
        assert set(problem) == {"index", "a", "c"}
        assert problem["a"] * problem["a"] == problem["c"]


def test_generate_problems_squ_requires_a_value() -> None:
    params = {"paper_size": "A4", "command_type": "squ", "num": 1}
    with pytest.raises(ValueError, match="a_value .* is required for the 'squ' command"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_pi_returns_valid_pi_multiplication_problems(renderer_name: str) -> None:
    params = {"paper_size": "A4", "command_type": "pi", "num": 5, "a_value": 3}
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 5
    for problem in problems:
        assert set(problem) == {"index", "a", "c"}
        assert problem["c"] == round(problem["a"] * nuts_calc_tex.PI_MULTIPLIER, 2)


def test_generate_problems_pi_requires_a_value() -> None:
    params = {"paper_size": "A4", "command_type": "pi", "num": 1}
    with pytest.raises(ValueError, match="a_value .* is required for the 'pi' command"):
        problem_generation.generate_problems(params, "latex")


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_frac_returns_valid_fraction_problems(renderer_name: str) -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 8,
        "numerator_digits": 1, "denominator_digits": 1, "operator": ["add"],
    }
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 8
    for problem in problems:
        assert set(problem) == {"index", "a", "b", "operator", "c", "mixed_number_display"}
        assert problem["operator"] == "add"
        a = Fraction(
            problem["a"]["whole"] * problem["a"]["denominator"] + problem["a"]["numerator"],
            problem["a"]["denominator"],
        )
        b = Fraction(
            problem["b"]["whole"] * problem["b"]["denominator"] + problem["b"]["numerator"],
            problem["b"]["denominator"],
        )
        c = Fraction(problem["c"]["numerator"], problem["c"]["denominator"])
        assert a + b == c


def test_generate_problems_frac_rejects_digits_out_of_range() -> None:
    params = {"paper_size": "A4", "command_type": "frac", "num": 1, "numerator_digits": 4}
    with pytest.raises(ValueError, match="numerator_digits must be between"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_rejects_same_and_different_denominator_combo() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 1,
        "same_denominator": True, "different_denominators": True,
    }
    with pytest.raises(ValueError, match="cannot be combined"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_rejects_proper_operands_digit_violation() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 1,
        "proper_operands": True, "numerator_digits": 2, "denominator_digits": 1,
    }
    with pytest.raises(ValueError, match="proper_operands requires"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_rejects_fraction_form_with_non_add_sub_operator() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 1,
        "operator": ["mul"], "a_fraction_form": "mixed",
    }
    with pytest.raises(ValueError, match="require operator="):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_rejects_improper_fraction_form() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 1,
        "operator": ["add"], "a_fraction_form": "improper",
    }
    with pytest.raises(ValueError, match="do not support 'improper'"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_reducible_mode_requires_mul_div_operator() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 1,
        "operator": ["add"], "reducible_mode": "required",
    }
    with pytest.raises(ValueError, match="reducible_mode only supports"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_frac_reducible_mode_required_yields_reducible_products() -> None:
    params = {
        "paper_size": "A4", "command_type": "frac", "num": 5,
        "operator": ["mul"], "numerator_digits": 2, "denominator_digits": 2,
        "reducible_mode": "required",
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 5
    for problem in problems:
        raw_numerator = problem["a"]["numerator"] * problem["b"]["numerator"]
        raw_denominator = problem["a"]["denominator"] * problem["b"]["denominator"]
        assert math.gcd(raw_numerator, raw_denominator) > 1


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_mixed_returns_valid_mixed_problems(renderer_name: str) -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 6,
        "a_kind": ["int"], "b_kind": ["int"], "operator": ["add"],
    }
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 6
    for problem in problems:
        assert set(problem) == {"index", "operands", "operators", "mixed", "result"}
        assert problem["mixed"] is False
        assert problem["operators"] == ["add"]
        assert len(problem["operands"]) == 2
        a = Fraction(
            problem["operands"][0]["value"]["numerator"], problem["operands"][0]["value"]["denominator"],
        )
        b = Fraction(
            problem["operands"][1]["value"]["numerator"], problem["operands"][1]["value"]["denominator"],
        )
        result = Fraction(problem["result"]["numerator"], problem["result"]["denominator"])
        assert a + b == result


def test_generate_problems_mixed_rejects_digits_out_of_range() -> None:
    params = {"paper_size": "A4", "command_type": "mixed", "num": 1, "denominator_digits": 5}
    with pytest.raises(ValueError, match="denominator_digits must be between"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_rejects_decimal_places_out_of_range() -> None:
    params = {"paper_size": "A4", "command_type": "mixed", "num": 1, "decimal_places": 3}
    with pytest.raises(ValueError, match="decimal_places must be between"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_rejects_terms_min_greater_than_terms_max() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 1,
        "terms_min": 4, "terms_max": 2,
    }
    with pytest.raises(ValueError, match="terms_min must be less than or equal to terms_max"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_terms_family_returns_multi_term_problems() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 4,
        "a_kind": ["int"], "b_kind": ["int"], "operator": ["add"],
        "terms": 4,
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 4
    for problem in problems:
        assert len(problem["operands"]) == 4
        assert len(problem["operators"]) == 3


def test_generate_problems_mixed_reducible_mode_requires_mul_div_operator() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 1,
        "operator": ["add"], "a_kind": ["fraction"], "b_kind": ["int"],
        "reducible_mode": "required",
    }
    with pytest.raises(ValueError, match="reducible_mode only supports"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_reducible_mode_rejects_terms_combo() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 1,
        "operator": ["mul"], "a_kind": ["fraction"], "b_kind": ["int"],
        "reducible_mode": "required", "terms": 3,
    }
    with pytest.raises(ValueError, match="cannot be combined with terms"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_reducible_mode_requires_fraction_int_pairing() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 1,
        "operator": ["mul"], "a_kind": ["fraction"], "b_kind": ["fraction"],
        "reducible_mode": "required",
    }
    with pytest.raises(ValueError, match="requires exactly one"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_mixed_reducible_mode_required_yields_reducible_products() -> None:
    params = {
        "paper_size": "A4", "command_type": "mixed", "num": 5,
        "operator": ["mul"], "a_kind": ["fraction"], "b_kind": ["int"],
        "numerator_digits": 2, "denominator_digits": 2,
        "reducible_mode": "required",
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 5
    for problem in problems:
        a_operand, b_operand = problem["operands"]
        raw_numerator = a_operand["raw_numerator"] * b_operand["raw_numerator"]
        raw_denominator = a_operand["raw_denominator"] * b_operand["raw_denominator"]
        assert math.gcd(raw_numerator, raw_denominator) > 1


def _operand_value(operand: dict) -> Fraction:
    return Fraction(
        operand["whole"] * operand["denominator"] + operand["numerator"], operand["denominator"],
    )


@pytest.mark.parametrize("renderer_name", ["reportlab", "latex"])
def test_generate_problems_compare_defaults_to_fraction_vs_fraction(renderer_name: str) -> None:
    """issue #171: with no a_kind/b_kind given, compare keeps its original
    fraction-vs-fraction-only behavior."""
    params = {
        "paper_size": "A4", "command_type": "compare", "num": 8,
        "numerator_digits": 1, "denominator_digits": 1,
    }
    problems = problem_generation.generate_problems(params, renderer_name)
    assert len(problems) == 8
    for problem in problems:
        assert set(problem) == {"index", "a", "b", "relation"}
        assert problem["a"]["kind"] == "fraction"
        assert problem["b"]["kind"] == "fraction"
        assert problem["relation"] in ("<", ">")
        assert (problem["relation"] == "<") == (_operand_value(problem["a"]) < _operand_value(problem["b"]))


def test_generate_problems_compare_supports_int_decimal_fraction_kind_mixing() -> None:
    params = {
        "paper_size": "A4", "command_type": "compare", "num": 15,
        "numerator_digits": 1, "denominator_digits": 1, "decimal_places": 1,
        "a_kind": ["int", "decimal", "fraction"], "b_kind": ["int", "decimal", "fraction"],
    }
    problems = problem_generation.generate_problems(params, "latex")
    assert len(problems) == 15
    for problem in problems:
        assert problem["a"]["kind"] in ("int", "decimal", "fraction")
        assert problem["b"]["kind"] in ("int", "decimal", "fraction")
        assert (problem["relation"] == "<") == (_operand_value(problem["a"]) < _operand_value(problem["b"]))


def test_generate_problems_compare_rejects_digits_out_of_range() -> None:
    params = {"paper_size": "A4", "command_type": "compare", "num": 1, "numerator_digits": 4}
    with pytest.raises(ValueError, match="numerator_digits must be between"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_compare_rejects_decimal_places_out_of_range() -> None:
    params = {"paper_size": "A4", "command_type": "compare", "num": 1, "decimal_places": 3}
    with pytest.raises(ValueError, match="decimal_places must be between"):
        problem_generation.generate_problems(params, "latex")


def test_generate_problems_compare_pattern_requires_fraction_kinds() -> None:
    params = {
        "paper_size": "A4", "command_type": "compare", "num": 1,
        "a_kind": ["int"], "comparison_pattern": "same-denominator",
    }
    with pytest.raises(ValueError, match="comparison_pattern requires"):
        problem_generation.generate_problems(params, "latex")
