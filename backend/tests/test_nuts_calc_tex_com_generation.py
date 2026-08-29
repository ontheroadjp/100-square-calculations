"""Unit tests for nuts_calc_tex.py's `com` problem-generation logic (issue #22).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

GENERATION_SAMPLE_SIZE = 200


def test_generate_com_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_com_problems(target=10, order=4, start_index=11)
    assert [problem.index for problem in problems] == [11, 12, 13, 14]


def test_generate_com_problems_complement_sums_to_target() -> None:
    target = 100
    problems = tex_module.generate_com_problems(target, order=GENERATION_SAMPLE_SIZE, start_index=1)
    for problem in problems:
        assert problem.a + problem.c == target
        assert problem.target == target
        assert 1 <= problem.a < target
        assert 0 < problem.c < target


def test_generate_com_problems_a_stays_within_target_range() -> None:
    target = 5
    problems = tex_module.generate_com_problems(target, order=GENERATION_SAMPLE_SIZE, start_index=1)
    observed_values = {problem.a for problem in problems}
    assert observed_values <= set(range(1, target))


def test_build_com_block_tex_blank_hides_answer() -> None:
    problem = tex_module.ComProblem(index=1, a=37, target=100, c=63)
    blank_tex = tex_module.build_com_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_com_block_tex(problem, show_answer=True)
    assert '63' not in blank_tex
    assert '\\underline' not in blank_tex
    # Pattern 2 now emits via the shared \boxedblankeq / \opspace / \boxedblank
    # components (issue #265) instead of a raw $...$ f-string.
    assert blank_tex == (
        "1) \\boxedblankeq{37 \\opspace + \\opspace "
        f"{tex_module.BOXED_BLANK_OPERAND_TEX} \\opspace = \\opspace 100}}"
    )
    assert tex_module.BOXED_BLANK_OPERAND_TEX in blank_tex
    assert tex_module.BLANK_ANSWER_TEX not in blank_tex
    assert filled_tex == "1) \\boxedblankeq{37 \\opspace + \\opspace 63 \\opspace = \\opspace 100}"


def test_build_com_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.ComProblem(index=1, a=37, target=100, c=63)]
    page2 = [tex_module.ComProblem(index=2, a=8, target=100, c=92)]
    rows = tex_module.build_com_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 37, 100, 63],
        [2, 2, 8, 100, 92],
    ]
