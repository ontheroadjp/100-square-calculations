"""Unit tests for nuts_calc_tex.py's `aBc` (mental arithmetic statement)
problem-generation logic (issue #25).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_abc_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_abc_problems(order=4, start_index=11)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_abc_problems_returns_requested_order_count() -> None:
    problems = tex_module.generate_abc_problems(order=7, start_index=1)
    assert len(problems) == 7


def test_generate_abc_problems_digits_are_within_zero_to_nine() -> None:
    problems = tex_module.generate_abc_problems(order=50, start_index=1)
    for problem in problems:
        for digit in (problem.a, problem.b, problem.c, problem.d):
            assert 0 <= digit <= 9


def test_abc_problem_answer_sums_shifted_digit_pairs() -> None:
    problem = tex_module.AbcProblem(index=1, a=1, b=2, c=3, d=4)
    assert problem.answer == 120 + 34


def test_abc_problem_abcd_display_renders_all_four_digits_including_leading_zero() -> None:
    problem = tex_module.AbcProblem(index=1, a=0, b=2, c=3, d=4)
    assert problem.abcd_display == '0234'


def test_build_abc_block_tex_blank_hides_answer() -> None:
    problem = tex_module.AbcProblem(index=1, a=1, b=2, c=3, d=4)
    blank_tex = tex_module.build_abc_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_abc_block_tex(problem, show_answer=True)
    assert '154' not in blank_tex
    assert '1234 \\Rightarrow \\underline' in blank_tex
    assert '1234 \\Rightarrow 154$' in filled_tex


def test_build_abc_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.AbcProblem(index=1, a=1, b=2, c=3, d=4),
        tex_module.AbcProblem(index=2, a=0, b=0, c=0, d=1),
    ]
    assert tex_module.build_abc_bottom_answer_tex(problems) == '(1) 154 \\quad (2) 1'


def test_build_abc_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.AbcProblem(index=1, a=1, b=2, c=3, d=4)]
    page2 = [tex_module.AbcProblem(index=2, a=0, b=0, c=0, d=1)]
    rows = tex_module.build_abc_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 1, 2, 3, 4, 154],
        [2, 2, 0, 0, 0, 1, 1],
    ]
