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
    assert '\\underline' not in blank_tex
    assert '2 + 3' in blank_tex
    assert '2 + 3 = \\hspace{1.5em}$' in blank_tex
    assert '2 + 3 = 5' in filled_tex


def test_build_horizontal_intermediate_block_tex_blank_hides_answer_without_underline() -> None:
    problem = tex_module.OpeProblem(index=1, a=23, b=4, operator='mul', c=92)
    blank_tex = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=True)
    assert '92' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '23 \\times 4 \\Rightarrow 0812 \\Rightarrow \\hspace{1.5em}$' in blank_tex
    assert '23 \\times 4 \\Rightarrow 0812 \\Rightarrow 92$' in filled_tex


def test_build_vertical_block_tex_div_uses_stage_zero_for_blank() -> None:
    problem = tex_module.OpeProblem(index=1, a=100, b=10, operator='div', c=10)
    blank_tex = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_vertical_block_tex(problem, show_answer=True)
    assert 'stage=0' in blank_tex
    assert 'stage=0' not in filled_tex


def test_build_vertical_block_tex_positions_operator_one_digit_left_of_numbers() -> None:
    problem = tex_module.OpeProblem(index=1, a=23, b=4, operator='add', c=27)
    blank_tex = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_vertical_block_tex(problem, show_answer=True)
    layout_options = 'voperator=bottom,columnwidth=2ex'

    assert f'\\opset{{{layout_options}' in blank_tex
    assert f'\\opset{{{layout_options}}}' in filled_tex


def test_build_ope_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.OpeProblem(index=1, a=2, b=3, operator='add', c=5)]
    page2 = [tex_module.OpeProblem(index=2, a=9, b=4, operator='sub', c=5)]
    rows = tex_module.build_ope_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 2, 'add', 3, 5],
        [2, 2, 9, 'sub', 4, 5],
    ]


def test_paren_stage_add_returns_sum() -> None:
    assert tex_module.paren_stage_add(3, 4) == 7


def test_paren_stage_sub_returns_none_for_non_positive_result() -> None:
    assert tex_module.paren_stage_sub(3, 4) is None
    assert tex_module.paren_stage_sub(4, 3) == 1


def test_paren_stage_mul_returns_product() -> None:
    assert tex_module.paren_stage_mul(6, 7) == 42


def test_paren_stage_div_returns_none_for_inexact_or_zero_divisor() -> None:
    assert tex_module.paren_stage_div(10, 0) is None
    assert tex_module.paren_stage_div(10, 3) is None
    assert tex_module.paren_stage_div(10, 5) == 2


def test_generate_paren_ope_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_paren_ope_problems(
        [5], [3], [2], ['add'], order=4, start_index=11
    )
    assert [problem.index for problem in problems] == [11, 12, 13, 14]
    # op_left == op_right == 'add' is associative, so every problem's final
    # result is 5 + 3 + 2 == 10 regardless of which pair gets parenthesized.
    assert [(p.a, p.b, p.c, p.result) for p in problems] == [(5, 3, 2, 10)] * 4
    for problem in problems:
        assert (problem.inner, problem.position) in [(8, 'left'), (5, 'right')]


def test_generate_paren_ope_problems_satisfies_both_stage_constraints_for_each_position() -> None:
    nums_a = list(range(10, 100))
    nums_bc = list(range(1, 10))
    problems = tex_module.generate_paren_ope_problems(
        nums_a, nums_bc, nums_bc, ['mul', 'div'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    positions_seen = set()
    for problem in problems:
        positions_seen.add(problem.position)
        assert problem.op_left in ('mul', 'div')
        assert problem.op_right in ('mul', 'div')
        if problem.position == 'left':
            assert problem.inner == tex_module.PAREN_STAGE_FUNCTIONS[problem.op_left](problem.a, problem.b)
            combined = tex_module.PAREN_STAGE_FUNCTIONS[problem.op_right](problem.inner, problem.c)
        else:
            assert problem.inner == tex_module.PAREN_STAGE_FUNCTIONS[problem.op_right](problem.b, problem.c)
            combined = tex_module.PAREN_STAGE_FUNCTIONS[problem.op_left](problem.a, problem.inner)
        assert combined == problem.result
    assert positions_seen == {'left', 'right'}  # both should appear across this many samples


def test_generate_paren_ope_problems_mix_only_uses_the_four_base_operators() -> None:
    nums = list(range(1, 10))
    problems = tex_module.generate_paren_ope_problems(
        nums, nums, nums, ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    operators_used = {problem.op_left for problem in problems} | {problem.op_right for problem in problems}
    assert operators_used <= {'add', 'sub', 'mul', 'div'}
    assert 'mix' not in operators_used


def test_generate_paren_ope_problems_raises_when_no_valid_triple_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.generate_paren_ope_problems([1], [9], [9], ['sub'], order=1, start_index=1)


def test_build_paren_ope_block_tex_left_position_parenthesizes_a_and_b() -> None:
    problem = tex_module.ParenOpeProblem(
        index=1, a=3, b=5, c=2, op_left='add', op_right='mul', position='left', inner=8, result=16
    )
    blank_tex = tex_module.build_paren_ope_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_paren_ope_block_tex(problem, show_answer=True)
    assert '= 16$' not in blank_tex
    assert '(3 + 5) \\times 2 = \\hspace{1.5em}$' in blank_tex
    assert '(3 + 5) \\times 2 = 16$' in filled_tex


def test_build_paren_ope_block_tex_right_position_parenthesizes_b_and_c() -> None:
    problem = tex_module.ParenOpeProblem(
        index=1, a=3, b=5, c=2, op_left='add', op_right='mul', position='right', inner=10, result=13
    )
    filled_tex = tex_module.build_paren_ope_block_tex(problem, show_answer=True)
    assert '3 + (5 \\times 2) = 13$' in filled_tex


def test_build_paren_ope_bottom_answer_tex_lists_results() -> None:
    problems = [
        tex_module.ParenOpeProblem(
            index=1, a=3, b=5, c=2, op_left='add', op_right='mul', position='left', inner=8, result=16,
        ),
        tex_module.ParenOpeProblem(
            index=2, a=9, b=4, c=1, op_left='sub', op_right='add', position='left', inner=5, result=6,
        ),
    ]
    assert tex_module.build_paren_ope_bottom_answer_tex(problems) == '(1) 16 \\quad (2) 6'


def test_build_paren_ope_csv_rows_has_one_row_per_problem() -> None:
    page1 = [
        tex_module.ParenOpeProblem(
            index=1, a=3, b=5, c=2, op_left='add', op_right='mul', position='left', inner=8, result=16,
        )
    ]
    page2 = [
        tex_module.ParenOpeProblem(
            index=2, a=9, b=4, c=1, op_left='sub', op_right='add', position='right', inner=5, result=4,
        )
    ]
    rows = tex_module.build_paren_ope_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 3, 'add', 5, 'mul', 2, 'left', 8, 16],
        [2, 2, 9, 'sub', 4, 'add', 1, 'right', 5, 4],
    ]


def test_generate_missing_value_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_missing_value_problems(
        [5], [3], ['add'], order=4, start_index=11
    )
    assert [problem.index for problem in problems] == [11, 12, 13, 14]
    assert [(problem.a, problem.b, problem.c) for problem in problems] == [(5, 3, 8)] * 4


def test_generate_missing_value_problems_satisfies_a_op_b_equals_c_for_every_operator() -> None:
    nums_a = list(range(10, 100))
    nums_b = list(range(1, 10))
    problems = tex_module.generate_missing_value_problems(
        nums_a, nums_b, ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    for problem in problems:
        a, b, c = tex_module.CALC_FUNCTIONS[problem.operator](problem.a, problem.b, nums_a, nums_b)
        assert (a, b, c) == (problem.a, problem.b, problem.c)


def test_generate_missing_value_problems_distributes_blank_across_a_and_b() -> None:
    problems = tex_module.generate_missing_value_problems(
        list(range(10, 100)), list(range(1, 10)), ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    blanks_seen = {problem.blank for problem in problems}
    assert blanks_seen == {'a', 'b'}


def test_generate_missing_value_problems_never_blanks_the_result() -> None:
    # 'c' (the result) is deliberately excluded from blank candidates:
    # hiding it would be indistinguishable from plain `ope`'s
    # always-hide-the-answer output, not a genuine missing-number puzzle.
    problems = tex_module.generate_missing_value_problems(
        list(range(10, 100)), list(range(1, 10)), ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    assert all(problem.blank != 'c' for problem in problems)


def test_generate_missing_value_problems_mix_only_uses_the_four_base_operators() -> None:
    nums = list(range(1, 10))
    problems = tex_module.generate_missing_value_problems(
        nums, nums, ['mix'], order=GENERATION_SAMPLE_SIZE, start_index=1
    )
    operators_used = {problem.operator for problem in problems}
    assert operators_used <= {'add', 'sub', 'mul', 'div'}
    assert 'mix' not in operators_used


def test_build_missing_value_block_tex_boxes_only_the_blank_position() -> None:
    problem = tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='b')
    blank_tex = tex_module.build_missing_value_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_missing_value_block_tex(problem, show_answer=True)

    assert blank_tex == f"1) $2 + {tex_module.BOXED_BLANK_TEX} = 5$"
    assert filled_tex == "1) $2 + 3 = 5$"


def test_build_missing_value_block_tex_boxes_a_when_blank_is_a() -> None:
    problem = tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='a')
    blank_tex = tex_module.build_missing_value_block_tex(problem, show_answer=False)
    assert blank_tex == f"1) ${tex_module.BOXED_BLANK_TEX} + 3 = 5$"


def test_build_missing_value_block_tex_always_shows_the_result() -> None:
    problem = tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='a')
    blank_tex = tex_module.build_missing_value_block_tex(problem, show_answer=False)
    assert '= 5$' in blank_tex
    assert tex_module.BOXED_BLANK_TEX not in blank_tex.split('=')[-1]


def test_build_missing_value_bottom_answer_tex_returns_the_blanked_value() -> None:
    problems = [
        tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='a'),
        tex_module.MissingValueProblem(index=2, a=9, b=4, operator='sub', c=5, blank='b'),
    ]
    assert tex_module.build_missing_value_bottom_answer_tex(problems) == '(1) 2 \\quad (2) 4'


def test_build_missing_value_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='b')]
    page2 = [tex_module.MissingValueProblem(index=2, a=9, b=4, operator='sub', c=5, blank='a')]
    rows = tex_module.build_missing_value_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 2, 'add', 3, 5, 'b'],
        [2, 2, 9, 'sub', 4, 5, 'a'],
    ]
