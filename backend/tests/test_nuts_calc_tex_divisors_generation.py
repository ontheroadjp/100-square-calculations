"""Unit tests for nuts_calc_tex.py's `divisors` (divisor-listing) problem-
generation logic (issue #94).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_divisors_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_divisors_problems(nums_a=[12], order=4, start_index=11)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_divisors_problems_draws_from_nums_a() -> None:
    problems = tex_module.generate_divisors_problems(nums_a=[12, 12, 12], order=5, start_index=1)
    assert all(problem.a == 12 for problem in problems)


def test_generate_divisors_problems_lists_all_divisors_ascending() -> None:
    problems = tex_module.generate_divisors_problems(nums_a=[12], order=1, start_index=1)
    assert problems[0].divisors == [1, 2, 3, 4, 6, 12]


def test_generate_divisors_problems_prime_number_has_two_divisors() -> None:
    problems = tex_module.generate_divisors_problems(nums_a=[7], order=1, start_index=1)
    assert problems[0].divisors == [1, 7]


def test_generate_divisors_problems_one_has_single_divisor() -> None:
    problems = tex_module.generate_divisors_problems(nums_a=[1], order=1, start_index=1)
    assert problems[0].divisors == [1]


def test_build_divisors_block_tex_blank_hides_list() -> None:
    problem = tex_module.DivisorsProblem(index=1, a=12, divisors=[1, 2, 3, 4, 6, 12])
    blank_tex = tex_module.build_divisors_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_divisors_block_tex(problem, show_answer=True)
    assert '6, 12' not in blank_tex
    assert '\\hspace{1.5em}' in blank_tex
    assert '\\arroweq{12 \\opspace \\Rightarrow \\opspace \\hspace{1.5em}}' in blank_tex
    assert '\\arroweq{12 \\opspace \\Rightarrow \\opspace 1, 2, 3, 4, 6, 12}' in filled_tex


def test_build_divisors_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.DivisorsProblem(index=1, a=12, divisors=[1, 2, 3, 4, 6, 12]),
        tex_module.DivisorsProblem(index=2, a=7, divisors=[1, 7]),
    ]
    assert tex_module.build_divisors_bottom_answer_tex(problems) == '(1) 1, 2, 3, 4, 6, 12 \\quad (2) 1, 7'


def test_build_divisors_csv_rows_joins_divisors_with_spaces() -> None:
    page1 = [tex_module.DivisorsProblem(index=1, a=12, divisors=[1, 2, 3, 4, 6, 12])]
    page2 = [tex_module.DivisorsProblem(index=2, a=7, divisors=[1, 7])]
    rows = tex_module.build_divisors_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 12, '1 2 3 4 6 12'],
        [2, 2, 7, '1 7'],
    ]
