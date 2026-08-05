"""Unit tests for nuts_calc_tex.py's `pi` (multiplication by pi) problem-generation
logic (issue #27).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_pi_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_pi_problems(start_num=3, order=4, start_index=11, descend=False, shuffle=False)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_pi_problems_default_order_is_ascending_from_start_num() -> None:
    problems = tex_module.generate_pi_problems(start_num=5, order=4, start_index=1, descend=False, shuffle=False)
    assert [problem.a for problem in problems] == [5, 6, 7, 8]
    for problem in problems:
        assert problem.c == round(problem.a * tex_module.PI_MULTIPLIER, 2)


def test_generate_pi_problems_descend_reverses_sequence_order() -> None:
    problems = tex_module.generate_pi_problems(start_num=1, order=9, start_index=1, descend=True, shuffle=False)
    assert [problem.a for problem in problems] == list(range(9, 0, -1))


def test_generate_pi_problems_shuffle_uses_same_number_set() -> None:
    problems = tex_module.generate_pi_problems(start_num=1, order=9, start_index=1, descend=False, shuffle=True)
    assert sorted(problem.a for problem in problems) == list(range(1, 10))


def test_generate_pi_problems_order_can_exceed_nine() -> None:
    problems = tex_module.generate_pi_problems(start_num=1, order=12, start_index=1, descend=False, shuffle=False)
    assert [problem.a for problem in problems] == list(range(1, 13))
    assert problems[-1].c == round(12 * tex_module.PI_MULTIPLIER, 2)


def test_generate_pi_problems_rounds_away_float_artifacts() -> None:
    # a=5 and a=10 are known to produce IEEE 754 float artifacts for raw
    # a * 3.14 (e.g. 15.700000000000001); generation must round them away.
    problems = tex_module.generate_pi_problems(start_num=5, order=6, start_index=1, descend=False, shuffle=False)
    by_a = {problem.a: problem.c for problem in problems}
    assert by_a[5] == 15.7
    assert by_a[10] == 31.4


def test_build_pi_block_tex_blank_hides_answer() -> None:
    problem = tex_module.PiProblem(index=1, a=2, c=6.28)
    blank_tex = tex_module.build_pi_block_tex(problem, show_answer=False, reverse=False)
    filled_tex = tex_module.build_pi_block_tex(problem, show_answer=True, reverse=False)
    assert '6.28' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '2 \\times 3.14 = \\hspace{1.5em}' in blank_tex
    assert '2 \\times 3.14 = 6.28$' in filled_tex


def test_build_pi_block_tex_reverse_swaps_equation_sides() -> None:
    problem = tex_module.PiProblem(index=1, a=2, c=6.28)
    blank_tex = tex_module.build_pi_block_tex(problem, show_answer=False, reverse=True)
    filled_tex = tex_module.build_pi_block_tex(problem, show_answer=True, reverse=True)
    assert '6.28' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '\\hspace{1.5em} = 2 \\times 3.14$' in blank_tex
    assert '6.28 = 2 \\times 3.14$' in filled_tex


def test_build_pi_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.PiProblem(index=1, a=1, c=3.14),
        tex_module.PiProblem(index=2, a=2, c=6.28),
    ]
    assert tex_module.build_pi_bottom_answer_tex(problems) == '(1) 3.14 \\quad (2) 6.28'


def test_build_pi_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.PiProblem(index=1, a=1, c=3.14)]
    page2 = [tex_module.PiProblem(index=2, a=2, c=6.28)]
    rows = tex_module.build_pi_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 1, 3.14],
        [2, 2, 2, 6.28],
    ]
