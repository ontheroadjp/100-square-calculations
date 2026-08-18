"""Unit tests for nuts_calc_tex.py's `99` (times-table / kuku) problem-generation
logic (issue #24).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_kuku_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_kuku_problems(a_value=3, order=4, start_index=11, descend=False, shuffle=False)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_kuku_problems_default_order_is_ascending_one_to_order() -> None:
    problems = tex_module.generate_kuku_problems(a_value=7, order=9, start_index=1, descend=False, shuffle=False)
    assert [problem.b for problem in problems] == list(range(1, 10))
    for problem in problems:
        assert problem.a == 7
        assert problem.c == 7 * problem.b


def test_generate_kuku_problems_descend_reverses_multiplier_order() -> None:
    problems = tex_module.generate_kuku_problems(a_value=5, order=9, start_index=1, descend=True, shuffle=False)
    assert [problem.b for problem in problems] == list(range(9, 0, -1))


def test_generate_kuku_problems_shuffle_uses_same_multiplier_set() -> None:
    problems = tex_module.generate_kuku_problems(a_value=4, order=9, start_index=1, descend=False, shuffle=True)
    assert sorted(problem.b for problem in problems) == list(range(1, 10))


def test_generate_kuku_problems_wraps_multiplier_at_nine_when_order_exceeds_nine() -> None:
    # issue #152: order = rows * columns can exceed 9, but only genuine kuku
    # facts (1-9) are valid, so the multiplier must wrap back to x1 instead
    # of continuing past x9 (mirrors nuts_calc.py's fix in issue #149,
    # nuts_calc.py:492-493).
    problems = tex_module.generate_kuku_problems(a_value=2, order=12, start_index=1, descend=False, shuffle=False)
    assert [problem.b for problem in problems] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3]
    assert problems[-1].c == 2 * 3


def test_generate_kuku_problems_descend_wraps_back_to_nine_when_order_exceeds_nine() -> None:
    # issue #155: reversing the ascending-wrapped sequence misplaces the
    # wrap boundary (would start at 1 instead of 9). Descend must compute
    # the wrapped sequence directly so it starts at 9 and wraps back to 9
    # (not 1) after reaching 1.
    problems = tex_module.generate_kuku_problems(a_value=2, order=10, start_index=1, descend=True, shuffle=False)
    assert [problem.b for problem in problems] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 9]


def test_build_kuku_block_tex_blank_hides_answer() -> None:
    problem = tex_module.KukuProblem(index=1, a=3, b=4, c=12)
    blank_tex = tex_module.build_kuku_block_tex(problem, show_answer=False, reverse=False)
    filled_tex = tex_module.build_kuku_block_tex(problem, show_answer=True, reverse=False)
    assert '12' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '3 \\times 4 = \\hspace{1.5em}' in blank_tex
    assert '3 \\times 4 = 12$' in filled_tex


def test_build_kuku_block_tex_reverse_swaps_equation_sides() -> None:
    problem = tex_module.KukuProblem(index=1, a=3, b=4, c=12)
    blank_tex = tex_module.build_kuku_block_tex(problem, show_answer=False, reverse=True)
    filled_tex = tex_module.build_kuku_block_tex(problem, show_answer=True, reverse=True)
    assert '12' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '\\hspace{1.5em} = 3 \\times 4$' in blank_tex
    assert '12 = 3 \\times 4$' in filled_tex


def test_build_kuku_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.KukuProblem(index=1, a=3, b=1, c=3),
        tex_module.KukuProblem(index=2, a=3, b=2, c=6),
    ]
    assert tex_module.build_kuku_bottom_answer_tex(problems) == '(1) 3 \\quad (2) 6'


def test_build_kuku_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.KukuProblem(index=1, a=3, b=1, c=3)]
    page2 = [tex_module.KukuProblem(index=2, a=3, b=2, c=6)]
    rows = tex_module.build_kuku_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 3, 1, 3],
        [2, 2, 3, 2, 6],
    ]
