"""Unit tests for nuts_calc_tex.py's `squ` (square numbers) problem-generation
logic (issue #26).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_squ_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_squ_problems(start_num=3, order=4, start_index=11, descend=False, shuffle=False)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_squ_problems_default_order_is_ascending_from_start_num() -> None:
    problems = tex_module.generate_squ_problems(start_num=5, order=4, start_index=1, descend=False, shuffle=False)
    assert [problem.a for problem in problems] == [5, 6, 7, 8]
    for problem in problems:
        assert problem.c == problem.a * problem.a


def test_generate_squ_problems_descend_reverses_sequence_order() -> None:
    problems = tex_module.generate_squ_problems(start_num=1, order=9, start_index=1, descend=True, shuffle=False)
    assert [problem.a for problem in problems] == list(range(9, 0, -1))


def test_generate_squ_problems_shuffle_uses_same_number_set() -> None:
    problems = tex_module.generate_squ_problems(start_num=1, order=9, start_index=1, descend=False, shuffle=True)
    assert sorted(problem.a for problem in problems) == list(range(1, 10))


def test_generate_squ_problems_order_can_exceed_nine() -> None:
    # order = rows * columns can exceed a fixed 9-item sequence (mirrors
    # nuts_calc.py's order = rows behavior, see nuts_calc.py:508-526).
    problems = tex_module.generate_squ_problems(start_num=1, order=12, start_index=1, descend=False, shuffle=False)
    assert [problem.a for problem in problems] == list(range(1, 13))
    assert problems[-1].c == 12 * 12


def test_build_squ_block_tex_blank_hides_answer() -> None:
    problem = tex_module.SquProblem(index=1, a=4, c=16)
    blank_tex = tex_module.build_squ_block_tex(problem, show_answer=False, reverse=False)
    filled_tex = tex_module.build_squ_block_tex(problem, show_answer=True, reverse=False)
    assert '16' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '4 \\times 4 = \\hspace{1.5em}' in blank_tex
    assert '4 \\times 4 = 16$' in filled_tex


def test_build_squ_block_tex_reverse_swaps_equation_sides() -> None:
    problem = tex_module.SquProblem(index=1, a=4, c=16)
    blank_tex = tex_module.build_squ_block_tex(problem, show_answer=False, reverse=True)
    filled_tex = tex_module.build_squ_block_tex(problem, show_answer=True, reverse=True)
    assert '16' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '\\hspace{1.5em} = 4 \\times 4$' in blank_tex
    assert '16 = 4 \\times 4$' in filled_tex


def test_build_squ_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.SquProblem(index=1, a=3, c=9),
        tex_module.SquProblem(index=2, a=4, c=16),
    ]
    assert tex_module.build_squ_bottom_answer_tex(problems) == '(1) 9 \\quad (2) 16'


def test_build_squ_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.SquProblem(index=1, a=3, c=9)]
    page2 = [tex_module.SquProblem(index=2, a=4, c=16)]
    rows = tex_module.build_squ_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 3, 9],
        [2, 2, 4, 16],
    ]
