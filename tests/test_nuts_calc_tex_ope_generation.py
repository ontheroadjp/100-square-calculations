"""Unit tests for nuts_calc_tex.py's `ope` problem-generation logic (issue #21).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import nuts_calc_tex as tex_module  # noqa: E402

GENERATION_SAMPLE_SIZE = 200


def test_calc_add_returns_sum() -> None:
    assert tex_module.calc_add(3, 4, [3], [4]) == (3, 4, 7)


def test_calc_sub_result_is_always_positive() -> None:
    nums_a = list(range(1, 10))
    nums_b = list(range(1, 10))
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_sub(1, 9, nums_a, nums_b)
        assert c == a - b
        assert c > 0


def test_calc_sub_succeeds_when_valid_pair_space_is_narrow() -> None:
    # Regression test (codex review, PR #29): nums_a x nums_b has 2000
    # candidate pairs but only one, (1000, 999), has a positive result.
    # Pure random resampling can exhaust MAX_OPERAND_RETRY_ATTEMPTS (1000)
    # without ever drawing it; calc_sub must still succeed deterministically.
    nums_a = list(range(1, 1001))
    nums_b = [999, 1000]
    a, b, c = tex_module.calc_sub(1, 1000, nums_a, nums_b)
    assert a - b == c > 0


def test_calc_sub_raises_when_no_positive_result_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.calc_sub(1, 9, [1, 2, 3], [5, 6, 7])


def test_calc_mul_returns_product() -> None:
    assert tex_module.calc_mul(6, 7, [6], [7]) == (6, 7, 42)


def test_calc_div_result_is_always_exact() -> None:
    nums_a = list(range(10, 100))
    nums_b = list(range(1, 10))
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_div(50, 3, nums_a, nums_b)
        assert b != 0
        assert a % b == 0
        assert c == a // b


def test_calc_div_succeeds_when_valid_pair_space_is_narrow() -> None:
    # Regression test (codex review, PR #29): nums_a x nums_b has a large
    # search space but only a handful of exact-division pairs. calc_div
    # must still succeed deterministically via find_exact_division_pair.
    nums_a = list(range(1, 1001))
    nums_b = [997]  # prime; only 997 itself divides evenly within nums_a
    a, b, c = tex_module.calc_div(1, 997, nums_a, nums_b)
    assert b != 0
    assert a % b == 0
    assert c == a // b


def test_calc_div_raises_when_no_exact_pair_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.calc_div(1, 2, [1], [2])


def test_find_exact_division_pair_returns_none_when_impossible() -> None:
    assert tex_module.find_exact_division_pair([1], [2]) is None


def test_generate_ope_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_ope_problems([5], [3], ['add'], order=4, start_index=11)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]
    assert [(problem.a, problem.b, problem.c) for problem in problems] == [(5, 3, 8)] * 4


def test_generate_ope_problems_mix_only_uses_the_four_base_operators() -> None:
    nums_a = list(range(10, 20))
    nums_b = list(range(1, 10))
    problems = tex_module.generate_ope_problems(
        nums_a, nums_b, ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    operators_used = {problem.operator for problem in problems}
    assert operators_used <= {'add', 'sub', 'mul', 'div'}
    assert 'mix' not in operators_used


def test_build_intermediate_memo_matches_memo_md_examples() -> None:
    # memo.md STEP 1 examples: 32x6 -> 18|12, 23x4 -> 08|12.
    assert tex_module.build_intermediate_memo(32, 6) == '1812'
    assert tex_module.build_intermediate_memo(23, 4) == '0812'


def test_build_horizontal_block_tex_blank_hides_answer() -> None:
    problem = tex_module.OpeProblem(index=1, a=2, b=3, operator='add', c=5)
    blank_tex = tex_module.build_horizontal_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    assert '= 5$' not in blank_tex
    assert '2 + 3' in blank_tex
    assert '2 + 3 = 5' in filled_tex


def test_build_vertical_block_tex_div_uses_stage_zero_for_blank() -> None:
    problem = tex_module.OpeProblem(index=1, a=100, b=10, operator='div', c=10)
    blank_tex = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_vertical_block_tex(problem, show_answer=True)
    assert 'stage=0' in blank_tex
    assert 'stage=0' not in filled_tex


def test_build_ope_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.OpeProblem(index=1, a=2, b=3, operator='add', c=5)]
    page2 = [tex_module.OpeProblem(index=2, a=9, b=4, operator='sub', c=5)]
    rows = tex_module.build_ope_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 2, 'add', 3, 5],
        [2, 2, 9, 'sub', 4, 5],
    ]
