"""Unit tests for nuts_calc_tex.py's `evenodd` (even/odd judgment) problem-
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


def test_generate_evenodd_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_evenodd_problems(nums_a=[4], order=4, start_index=11)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_evenodd_problems_draws_from_nums_a() -> None:
    problems = tex_module.generate_evenodd_problems(nums_a=[3, 3, 3], order=5, start_index=1)
    assert all(problem.a == 3 for problem in problems)


def test_generate_evenodd_problems_is_even_matches_parity() -> None:
    problems = tex_module.generate_evenodd_problems(nums_a=list(range(1, 10)), order=50, start_index=1)
    for problem in problems:
        assert problem.is_even == (problem.a % 2 == 0)


def test_evenodd_problem_label_is_ascii_even_or_odd() -> None:
    even_problem = tex_module.EvenOddProblem(index=1, a=6, is_even=True)
    odd_problem = tex_module.EvenOddProblem(index=2, a=7, is_even=False)
    assert even_problem.label == 'even'
    assert odd_problem.label == 'odd'


def test_build_evenodd_block_tex_blank_hides_label() -> None:
    problem = tex_module.EvenOddProblem(index=1, a=6, is_even=True)
    blank_tex = tex_module.build_evenodd_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_evenodd_block_tex(problem, show_answer=True)
    assert 'even' not in blank_tex
    assert '\\hspace{1.5em}' in blank_tex
    assert '\\arroweq{6 \\opspace \\Rightarrow \\opspace \\hspace{1.5em}}' in blank_tex
    assert '\\arroweq{6 \\opspace \\Rightarrow \\opspace \\mathrm{even}}' in filled_tex


def test_build_evenodd_block_tex_odd_label() -> None:
    problem = tex_module.EvenOddProblem(index=1, a=7, is_even=False)
    filled_tex = tex_module.build_evenodd_block_tex(problem, show_answer=True)
    assert '\\arroweq{7 \\opspace \\Rightarrow \\opspace \\mathrm{odd}}' in filled_tex


def test_build_evenodd_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.EvenOddProblem(index=1, a=6, is_even=True),
        tex_module.EvenOddProblem(index=2, a=7, is_even=False),
    ]
    assert tex_module.build_evenodd_bottom_answer_tex(problems) == '(1) even \\quad (2) odd'


def test_build_evenodd_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.EvenOddProblem(index=1, a=6, is_even=True)]
    page2 = [tex_module.EvenOddProblem(index=2, a=7, is_even=False)]
    rows = tex_module.build_evenodd_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 6, 'even'],
        [2, 2, 7, 'odd'],
    ]
