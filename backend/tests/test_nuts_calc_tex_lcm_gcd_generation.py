"""Unit tests for nuts_calc_tex.py's `lcm`/`gcd` (two-number-property)
problem-generation logic (issue #95).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import math
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_generate_number_pair_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_number_pair_problems(
        math.lcm, list(range(1, 10)), list(range(1, 10)), order=4, start_index=11,
    )
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_number_pair_problems_lcm_matches_math_lcm() -> None:
    problems = tex_module.generate_number_pair_problems(
        math.lcm, list(range(1, 10)), list(range(1, 10)), order=20, start_index=1,
    )
    for problem in problems:
        assert problem.c == math.lcm(problem.a, problem.b)


def test_generate_number_pair_problems_gcd_matches_math_gcd() -> None:
    problems = tex_module.generate_number_pair_problems(
        math.gcd, list(range(1, 10)), list(range(1, 10)), order=20, start_index=1,
    )
    for problem in problems:
        assert problem.c == math.gcd(problem.a, problem.b)


def test_build_number_pair_block_tex_blank_hides_answer() -> None:
    problem = tex_module.NumberPairProblem(index=1, a=6, b=8, c=24)
    blank_tex = tex_module.build_number_pair_block_tex(problem, show_answer=False, label='LCM')
    filled_tex = tex_module.build_number_pair_block_tex(problem, show_answer=True, label='LCM')
    assert '24' not in blank_tex
    assert blank_tex == (
        '1) \\horizontaleq{\\mathrm{LCM}(6, 8) \\opspace = \\opspace \\hspace{1.5em}}'
    )
    assert filled_tex == (
        '1) \\horizontaleq{\\mathrm{LCM}(6, 8) \\opspace = \\opspace 24}'
    )


def test_build_number_pair_block_tex_uses_given_label() -> None:
    problem = tex_module.NumberPairProblem(index=1, a=18, b=24, c=6)
    filled_tex = tex_module.build_number_pair_block_tex(problem, show_answer=True, label='GCD')
    assert filled_tex == (
        '1) \\horizontaleq{\\mathrm{GCD}(18, 24) \\opspace = \\opspace 6}'
    )


def test_build_number_pair_bottom_answer_tex_lists_answers_by_index() -> None:
    problems = [
        tex_module.NumberPairProblem(index=1, a=6, b=8, c=24),
        tex_module.NumberPairProblem(index=2, a=18, b=24, c=6),
    ]
    assert tex_module.build_number_pair_bottom_answer_tex(problems) == '(1) 24 \\quad (2) 6'


def test_build_number_pair_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.NumberPairProblem(index=1, a=6, b=8, c=24)]
    page2 = [tex_module.NumberPairProblem(index=2, a=18, b=24, c=6)]
    rows = tex_module.build_number_pair_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 6, 8, 24],
        [2, 2, 18, 24, 6],
    ]
