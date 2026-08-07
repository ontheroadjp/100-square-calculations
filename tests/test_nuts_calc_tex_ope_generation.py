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


def test_resolve_term_range_clamps_below_default_floor_to_two() -> None:
    assert tex_module.resolve_term_range(0, 1, False) == (2, 2)
    assert tex_module.resolve_term_range(1, 1, False) == (2, 2)


def test_resolve_term_range_clamps_below_parentheses_floor_to_three() -> None:
    assert tex_module.resolve_term_range(2, 2, True) == (3, 3)
    assert tex_module.resolve_term_range(1, 3, True) == (3, 3)


def test_resolve_term_range_clamps_above_ceiling_to_max_ope_terms() -> None:
    assert tex_module.resolve_term_range(50, 50, False) == (
        tex_module.MAX_OPE_TERMS, tex_module.MAX_OPE_TERMS,
    )


def test_resolve_term_range_leaves_in_range_values_untouched() -> None:
    assert tex_module.resolve_term_range(4, 6, False) == (4, 6)
    assert tex_module.resolve_term_range(4, 6, True) == (4, 6)


def test_build_tree_shape_produces_the_requested_leaf_count() -> None:
    for leaf_count in (1, 2, 3, 5, 8):
        tree = tex_module.build_tree_shape(leaf_count)
        assert len(tex_module.collect_leaves(tree)) == leaf_count


def test_build_tree_shape_matches_the_two_shapes_the_old_fixed_3_term_code_produced() -> None:
    # For leaf_count == 3, the only two possible splits (1/2 and 2/1)
    # reproduce exactly the two shapes generate_paren_ope_problems used to
    # produce (position='right'/'left' respectively).
    shapes_seen = set()
    for _ in range(GENERATION_SAMPLE_SIZE):
        tree = tex_module.build_tree_shape(3)
        left_leaves = len(tex_module.collect_leaves(tree.left))
        right_leaves = len(tex_module.collect_leaves(tree.right))
        shapes_seen.add((left_leaves, right_leaves))
    assert shapes_seen == {(1, 2), (2, 1)}


def test_evaluate_expr_tree_reuses_paren_stage_validity() -> None:
    invalid_tree = tex_module.ExprTreeNode(
        operator='sub',
        left=tex_module.ExprTreeNode(value=3),
        right=tex_module.ExprTreeNode(value=5),
    )
    assert tex_module.evaluate_expr_tree(invalid_tree) is None

    valid_tree = tex_module.ExprTreeNode(
        operator='add',
        left=tex_module.ExprTreeNode(value=3),
        right=tex_module.ExprTreeNode(
            operator='mul',
            left=tex_module.ExprTreeNode(value=5),
            right=tex_module.ExprTreeNode(value=2),
        ),
    )
    assert tex_module.evaluate_expr_tree(valid_tree) == 13


def test_render_expr_tree_wraps_every_internal_node_except_the_root() -> None:
    # 3 + (5 x 2), matching the shape the old fixed 3-term
    # build_paren_ope_block_tex would have produced for position='right'.
    tree = tex_module.ExprTreeNode(
        operator='add',
        left=tex_module.ExprTreeNode(value=3),
        right=tex_module.ExprTreeNode(
            operator='mul',
            left=tex_module.ExprTreeNode(value=5),
            right=tex_module.ExprTreeNode(value=2),
        ),
    )
    assert tex_module.build_tree_ope_expression_tex(tree) == '3 + (5 \\times 2)'
    assert tex_module.build_tree_ope_structure_text(tree) == '3 add (5 mul 2)'


def test_generate_tree_ope_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_tree_ope_problems(
        [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3, order=4, start_index=11,
    )
    assert [problem.index for problem in problems] == [11, 12, 13, 14]
    # All leaves are 5 (first) or 3 (rest) with only 'add', so every shape
    # sums to 5 + 3 + 3 == 11 regardless of tree structure.
    assert [problem.result for problem in problems] == [11] * 4


def test_generate_tree_ope_problems_result_matches_manual_tree_evaluation() -> None:
    nums_a = list(range(10, 100))
    nums_bc = list(range(1, 10))
    problems = tex_module.generate_tree_ope_problems(
        nums_a, nums_bc, ['mul', 'div'], mixed=True,
        terms_min=4, terms_max=4, order=GENERATION_SAMPLE_SIZE, start_index=1,
    )
    for problem in problems:
        assert len(problem.operands) == 4
        assert tex_module.evaluate_expr_tree(problem.tree) == problem.result


def test_generate_tree_ope_problems_mix_only_uses_the_four_base_operators() -> None:
    nums = list(range(1, 10))
    problems = tex_module.generate_tree_ope_problems(
        nums, nums, ['mix'], mixed=True, terms_min=3, terms_max=5,
        order=GENERATION_SAMPLE_SIZE, start_index=1,
    )
    operators_used = {operator for problem in problems for operator in problem.operators}
    assert operators_used <= {'add', 'sub', 'mul', 'div'}
    assert 'mix' not in operators_used


def test_generate_tree_ope_problems_raises_when_no_valid_tree_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.generate_tree_ope_problems(
            [1], [9], ['sub'], mixed=False, terms_min=3, terms_max=3, order=1, start_index=1,
        )


def test_build_tree_ope_bottom_answer_tex_lists_results() -> None:
    tree1 = tex_module.ExprTreeNode(
        operator='add', left=tex_module.ExprTreeNode(value=3), right=tex_module.ExprTreeNode(value=5),
    )
    tree2 = tex_module.ExprTreeNode(
        operator='sub', left=tex_module.ExprTreeNode(value=9), right=tex_module.ExprTreeNode(value=4),
    )
    problems = [
        tex_module.TreeOpeProblem(index=1, operands=[3, 5], operators=['add'], tree=tree1, result=8),
        tex_module.TreeOpeProblem(index=2, operands=[9, 4], operators=['sub'], tree=tree2, result=5),
    ]
    assert tex_module.build_tree_ope_bottom_answer_tex(problems) == '(1) 8 \\quad (2) 5'


def test_build_tree_ope_csv_rows_has_one_self_describing_row_per_problem() -> None:
    tree = tex_module.ExprTreeNode(
        operator='add',
        left=tex_module.ExprTreeNode(value=3),
        right=tex_module.ExprTreeNode(
            operator='mul',
            left=tex_module.ExprTreeNode(value=5),
            right=tex_module.ExprTreeNode(value=2),
        ),
    )
    page1 = [tex_module.TreeOpeProblem(index=1, operands=[3, 5, 2], operators=['add', 'mul'], tree=tree, result=13)]
    rows = tex_module.build_tree_ope_csv_rows([page1])
    assert rows == [[1, 1, 3, '3 add (5 mul 2)', 13]]


def test_evaluate_left_to_right_requires_every_intermediate_subtraction_to_stay_positive() -> None:
    # 10 - 3 - 8 would go negative at the second step even though the
    # overall operand list looks plausible; must reject, not just check
    # the final result.
    assert tex_module.evaluate_left_to_right([10, 3, 8], ['sub', 'sub']) is None
    assert tex_module.evaluate_left_to_right([10, 3, 2], ['sub', 'sub']) == 5


def test_evaluate_left_to_right_requires_every_intermediate_division_to_stay_exact() -> None:
    assert tex_module.evaluate_left_to_right([100, 10, 3], ['div', 'div']) is None
    assert tex_module.evaluate_left_to_right([100, 10, 2], ['div', 'div']) == 5


def test_split_into_precedence_groups_groups_consecutive_mul_div() -> None:
    groups, group_operators, connecting = tex_module.split_into_precedence_groups(
        [2, 3, 4, 5], ['add', 'mul', 'sub'],
    )
    assert groups == [[2], [3, 4], [5]]
    assert group_operators == [[], ['mul'], []]
    assert connecting == ['add', 'sub']


def test_evaluate_mixed_expression_respects_standard_precedence() -> None:
    # 2 + 3 x 4 == 14, not 20 (which strict left-to-right would give).
    assert tex_module.evaluate_mixed_expression([2, 3, 4], ['add', 'mul']) == 14


def test_evaluate_mixed_expression_returns_none_when_any_group_is_invalid() -> None:
    # 10 - (3 x 4) would need the group 3x4=12 subtracted from 10, going negative.
    assert tex_module.evaluate_mixed_expression([10, 3, 4], ['sub', 'mul']) is None


def test_generate_multi_term_ope_problems_single_operator_matches_left_to_right() -> None:
    problems = tex_module.generate_multi_term_ope_problems(
        [10], [1, 2], ['add'], mixed=False, terms_min=4, terms_max=4, order=5, start_index=1,
    )
    for problem in problems:
        assert len(problem.operands) == 4
        assert len(set(problem.operators)) == 1
        assert problem.result == tex_module.evaluate_left_to_right(problem.operands, problem.operators)


def test_generate_multi_term_ope_problems_mixed_uses_standard_precedence() -> None:
    problems = tex_module.generate_multi_term_ope_problems(
        [10, 20], [1, 2, 3], ['add', 'sub', 'mul'], mixed=True,
        terms_min=4, terms_max=4, order=GENERATION_SAMPLE_SIZE, start_index=1,
    )
    for problem in problems:
        assert problem.mixed is True
        assert problem.result == tex_module.evaluate_mixed_expression(problem.operands, problem.operators)


def test_generate_multi_term_ope_problems_raises_when_no_valid_sequence_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.generate_multi_term_ope_problems(
            [1], [9], ['sub'], mixed=False, terms_min=3, terms_max=3, order=1, start_index=1,
        )


def test_build_multi_term_ope_block_tex_renders_flat_without_parentheses() -> None:
    problem = tex_module.MultiTermOpeProblem(
        index=1, operands=[5, 3, 2], operators=['add', 'sub'], mixed=False, result=6,
    )
    blank_tex = tex_module.build_multi_term_ope_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_multi_term_ope_block_tex(problem, show_answer=True)
    expression_tex = filled_tex.split('$', 1)[1]
    assert '(' not in expression_tex and ')' not in expression_tex
    assert '5 + 3 - 2 = \\hspace{1.5em}$' in blank_tex
    assert '5 + 3 - 2 = 6$' in filled_tex


def test_build_multi_term_ope_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.MultiTermOpeProblem(index=1, operands=[5, 3, 2], operators=['add', 'sub'], mixed=False, result=6)]
    page2 = [tex_module.MultiTermOpeProblem(index=2, operands=[9, 4], operators=['mul'], mixed=True, result=36)]
    rows = tex_module.build_multi_term_ope_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 3, False, '5 add 3 sub 2', 6],
        [2, 2, 2, True, '9 mul 4', 36],
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
