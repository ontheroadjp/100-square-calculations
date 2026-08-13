"""Unit tests for nuts_calc_tex.py's `multiples` (multiples-listing) problem-
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


def test_generate_multiples_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_multiples_problems(nums_a=[6], order=4, start_index=11, count=3)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_multiples_problems_draws_from_nums_a() -> None:
    problems = tex_module.generate_multiples_problems(nums_a=[6, 6, 6], order=5, start_index=1, count=3)
    assert all(problem.a == 6 for problem in problems)


def test_generate_multiples_problems_lists_first_count_multiples() -> None:
    problems = tex_module.generate_multiples_problems(nums_a=[6], order=1, start_index=1, count=4)
    assert problems[0].multiples == [6, 12, 18, 24]


def test_generate_multiples_problems_respects_count() -> None:
    problems = tex_module.generate_multiples_problems(nums_a=[3], order=1, start_index=1, count=1)
    assert problems[0].multiples == [3]


def test_build_multiples_block_tex_blank_hides_list() -> None:
    problem = tex_module.MultiplesProblem(index=1, a=6, multiples=[6, 12, 18])
    blank_tex = tex_module.build_multiples_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_multiples_block_tex(problem, show_answer=True)
    assert '12' not in blank_tex
    assert '\\hspace{1.5em}' in blank_tex
    assert '6 \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '6 \\Rightarrow 6, 12, 18$' in filled_tex


def test_build_multiples_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.MultiplesProblem(index=1, a=6, multiples=[6, 12]),
        tex_module.MultiplesProblem(index=2, a=3, multiples=[3, 6]),
    ]
    assert tex_module.build_multiples_bottom_answer_tex(problems) == '(1) 6, 12 \\quad (2) 3, 6'


def test_build_multiples_csv_rows_joins_multiples_with_spaces() -> None:
    page1 = [tex_module.MultiplesProblem(index=1, a=6, multiples=[6, 12, 18])]
    page2 = [tex_module.MultiplesProblem(index=2, a=3, multiples=[3, 6, 9])]
    rows = tex_module.build_multiples_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 6, '6 12 18'],
        [2, 2, 3, '3 6 9'],
    ]
