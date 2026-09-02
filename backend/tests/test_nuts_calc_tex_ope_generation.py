"""Unit tests for nuts_calc_tex.py's `ope` problem-generation logic (issue #21).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

GENERATION_SAMPLE_SIZE = 200


def test_calc_add_returns_sum() -> None:
    assert tex_module.calc_add(3, 4, [3], [4]) == (3, 4, 7)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (12, 34, False),
        (15, 27, True),
        (95, 5, True),
        (100, 200, False),
    ],
)
def test_addition_has_carry_detects_any_digit_carry(a: int, b: int, expected: bool) -> None:
    assert tex_module.addition_has_carry(a, b) is expected


def test_calc_add_carry_prefers_matching_pair_in_requested_ranges() -> None:
    assert tex_module.calc_add(8, 2, [8], [2], carry=True) == (8, 2, 10)


def test_calc_add_no_carry_prefers_matching_pair_in_requested_ranges() -> None:
    assert tex_module.calc_add(3, 4, [3], [4], carry=False) == (3, 4, 7)


def test_calc_add_carry_fallback_ignores_impossible_bounds(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 1)

    a, b, c = tex_module.calc_add(4, 4, [1, 2, 3, 4], [1, 2, 3, 4], carry=True)

    assert tex_module.addition_has_carry(a, b)
    assert c == a + b
    assert (a, b) == (1, 9)


def test_calc_add_no_carry_fallback_ignores_impossible_bounds(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 1)

    a, b, c = tex_module.calc_add(9, 9, [9], [9], carry=False)

    assert not tex_module.addition_has_carry(a, b)
    assert c == a + b
    assert (a, b) == (1, 1)


@pytest.mark.parametrize("carry", [True, False])
def test_calc_add_fallback_preserves_operand_digit_widths(
        monkeypatch: pytest.MonkeyPatch, carry: bool,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)

    a, b, c = tex_module.calc_add(999, 9999, [999], [9999], carry=carry)

    assert len(str(a)) == 3
    assert len(str(b)) == 4
    assert tex_module.addition_has_carry(a, b) is carry
    assert c == a + b


@pytest.mark.parametrize(
    ("carry_mode", "expected_carry"),
    [('required', True), ('none', False)],
)
def test_generate_ope_problems_applies_addition_carry_filter(
        carry_mode: tex_module.CarryMode, expected_carry: bool,
    ) -> None:
    problems = tex_module.generate_ope_problems(
        list(range(1, 10)), list(range(1, 10)), ['add'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, carry_mode=carry_mode,
    )

    assert all(
        tex_module.addition_has_carry(problem.a, problem.b) is expected_carry
        for problem in problems
    )


@pytest.mark.parametrize(
    ("operator", "nums_a", "nums_b", "result_max"),
    [
        ("add", [999], [1], 1000),
        ("sub", [999], [1], 998),
        ("mul", [25], [4], 100),
        ("div", [999], [3], 333),
    ],
)
def test_generate_ope_problems_applies_result_max_to_every_operator(
        operator: str, nums_a: list[int], nums_b: list[int], result_max: int,
    ) -> None:
    problems = tex_module.generate_ope_problems(
        nums_a, nums_b, [operator], order=4, start_index=1,
        result_max=result_max,
    )

    assert all(problem.c <= result_max for problem in problems)


def test_generate_ope_problems_applies_result_max_to_displayed_decimal_value() -> None:
    problems = tex_module.generate_ope_problems(
        [999], [1], ["add"], order=1, start_index=1,
        a_decimal_places=1, b_decimal_places=1, result_max=100,
    )

    assert problems[0].c == 1000
    assert tex_module.ope_result_decimal_places("add", 1, 1) == 1


def test_generate_ope_problems_rejects_impossible_result_max() -> None:
    with pytest.raises(ValueError, match="satisfies --result-max"):
        tex_module.generate_ope_problems(
            [999], [2], ["add"], order=1, start_index=1, result_max=1000,
        )


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (8, 3, False),
        (12, 3, True),
        (18, 7, False),
        (100, 1, True),
    ],
)
def test_subtraction_has_borrow_detects_any_digit_borrow(
        a: int, b: int, expected: bool,
    ) -> None:
    assert tex_module.subtraction_has_borrow(a, b) is expected


def test_calc_sub_borrow_uses_10_to_19_minus_one_digit() -> None:
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_sub(9, 1, [1, 9], [1, 9], borrow=True)
        assert 10 <= a <= 19
        assert 1 <= b <= 9
        assert tex_module.subtraction_has_borrow(a, b)
        assert c == a - b > 0


def test_calc_sub_no_borrow_fallback_ignores_impossible_bounds(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)

    a, b, c = tex_module.calc_sub(10, 9, [10], [9], borrow=False)

    assert not tex_module.subtraction_has_borrow(a, b)
    assert c == a - b > 0


@pytest.mark.parametrize(
    ("nums_a", "nums_b"),
    [
        (list(range(10, 100)), list(range(1, 10))),  # 2-digit minuend
        (list(range(100, 1000)), list(range(1, 100))),  # 3-digit minuend
        (list(range(1000, 10000)), list(range(1, 1000))),  # 4-digit minuend
    ],
)
def test_calc_sub_borrow_respects_configured_multi_digit_range(
        nums_a: list[int], nums_b: list[int],
    ) -> None:
    # issue #92: borrow=True must sample within the caller's configured
    # range for multi-digit widths instead of always forcing 10-19.
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_sub(
            nums_a[0], nums_b[0], nums_a, nums_b, borrow=True,
        )
        assert min(nums_a) <= a <= max(nums_a)
        assert min(nums_b) <= b <= max(nums_b)
        assert tex_module.subtraction_has_borrow(a, b)
        assert c == a - b > 0


@pytest.mark.parametrize(
    ("a_width", "b_width"), [(2, 1), (3, 1), (4, 2)],
)
def test_calc_sub_borrow_fallback_preserves_operand_digit_widths(
        monkeypatch: pytest.MonkeyPatch, a_width: int, b_width: int,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)
    nums_a = [10 ** (a_width - 1)]
    nums_b = [10 ** (b_width - 1)]

    a, b, c = tex_module.calc_sub(nums_a[0], nums_b[0], nums_a, nums_b, borrow=True)

    assert len(str(a)) == a_width
    assert len(str(b)) == b_width
    assert tex_module.subtraction_has_borrow(a, b)
    assert c == a - b > 0


def test_calc_sub_borrow_keeps_grade1_teens_range_for_single_digit_bounds() -> None:
    # The mixed-carry grade-1 preset shares one 1-9/1-9 range across add and
    # sub, where no borrowing pair with a positive result exists -- calc_sub
    # must keep falling back to the teens-minus-one-digit sampling here.
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_sub(9, 1, list(range(1, 10)), list(range(1, 10)), borrow=True)
        assert 10 <= a <= 19
        assert 1 <= b <= 9
        assert tex_module.subtraction_has_borrow(a, b)
        assert c == a - b > 0


@pytest.mark.parametrize(
    ("carry_mode", "expected_condition"),
    [('required', True), ('none', False)],
)
def test_generate_add_sub_problems_applies_carry_and_borrow_filter(
        carry_mode: tex_module.CarryMode, expected_condition: bool,
    ) -> None:
    problems = tex_module.generate_ope_problems(
        list(range(1, 10)), list(range(1, 10)), ['add', 'sub'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, carry_mode=carry_mode,
    )

    for problem in problems:
        if problem.operator == 'add':
            assert tex_module.addition_has_carry(problem.a, problem.b) is expected_condition
        else:
            assert tex_module.subtraction_has_borrow(problem.a, problem.b) is expected_condition
            if expected_condition:
                assert 10 <= problem.a <= 19
                assert 1 <= problem.b <= 9


def test_generate_add_sub_mixed_carry_covers_all_four_conditions() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(1, 10)), list(range(1, 10)), ['add', 'sub'],
        order=2000, start_index=1, carry_mode='mixed',
    )

    observed = {
        (
            problem.operator,
            tex_module.addition_has_carry(problem.a, problem.b)
            if problem.operator == 'add'
            else tex_module.subtraction_has_borrow(problem.a, problem.b),
        )
        for problem in problems
    }
    assert observed == {('add', False), ('add', True), ('sub', False), ('sub', True)}
    for problem in problems:
        if problem.operator == 'sub' and tex_module.subtraction_has_borrow(problem.a, problem.b):
            assert 10 <= problem.a <= 19
            assert 1 <= problem.b <= 9


@pytest.mark.parametrize(
    ("carry_mode", "expected_condition"),
    [('required', True), ('none', False)],
)
def test_generate_add_sub_problems_applies_carry_and_borrow_filter_with_decimal_places(
        carry_mode: tex_module.CarryMode, expected_condition: bool,
    ) -> None:
    # issue #113: --carry-borrow/--no-carry-borrow determine carrying/
    # borrowing from the raw scaled integers, so decimal operands (equal
    # a_decimal_places/b_decimal_places, enforced by _init()) behave
    # identically to the integer case above.
    problems = tex_module.generate_ope_problems(
        list(range(1, 10)), list(range(1, 10)), ['add', 'sub'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, carry_mode=carry_mode,
        a_decimal_places=1, b_decimal_places=1,
    )

    for problem in problems:
        assert problem.a_decimal_places == 1
        assert problem.b_decimal_places == 1
        if problem.operator == 'add':
            assert tex_module.addition_has_carry(problem.a, problem.b) is expected_condition
        else:
            assert tex_module.subtraction_has_borrow(problem.a, problem.b) is expected_condition


def test_generate_ope_problems_decimal_carry_matches_illustrative_example() -> None:
    # 4.7 + 1.6 = 6.3 carries at the tenths digit (7 + 6 >= 10), matching the
    # grade-3/4 frontend/web preset examples that motivated #113.
    problems = tex_module.generate_ope_problems(
        [47], [16], ['add'],
        order=1, start_index=1, carry_mode='required',
        a_decimal_places=1, b_decimal_places=1,
    )

    problem = problems[0]
    assert (problem.a, problem.b, problem.c) == (47, 16, 63)
    assert tex_module.format_decimal_value(problem.a, problem.a_decimal_places) == "4.7"
    assert tex_module.format_decimal_value(problem.b, problem.b_decimal_places) == "1.6"
    assert tex_module.format_decimal_value(
        problem.c, tex_module.ope_result_decimal_places('add', 1, 1),
    ) == "6.3"


def test_generate_ope_problems_a_multiple_restricts_first_operand() -> None:
    # issue #331: --a-multiple filters nums_a to exact multiples before sampling.
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(1, 10)), ['add'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, a_multiple=10,
    )
    assert problems
    assert all(problem.a % 10 == 0 for problem in problems)


@pytest.mark.parametrize("operator", ['add', 'sub'])
def test_generate_ope_problems_tens_operands_stay_carry_free_and_bounded(operator: str) -> None:
    # issue #331: the grade-1 何十±何十 config (both operands multiples of 10,
    # carry_mode 'none', result_max 100) generates only 何十 pairs with no
    # digit-wise carry/borrow and an answer within 100.
    problems = tex_module.generate_ope_problems(
        list(range(10, 91)), list(range(10, 91)), [operator],
        order=GENERATION_SAMPLE_SIZE, start_index=1,
        carry_mode='none', result_max=100, a_multiple=10, b_multiple=10,
    )
    assert problems
    for problem in problems:
        assert problem.a % 10 == 0 and problem.b % 10 == 0
        assert problem.c <= 100
        if operator == 'add':
            assert not tex_module.addition_has_carry(problem.a, problem.b)
        else:
            assert problem.c > 0
            assert not tex_module.subtraction_has_borrow(problem.a, problem.b)


@pytest.mark.parametrize("multiple_kwargs", [{"a_multiple": 10}, {"b_multiple": 10}])
def test_generate_ope_problems_raises_when_multiple_filter_empties_range(
        multiple_kwargs: dict[str, int],
    ) -> None:
    # issue #331: a multiple with no representative in [min, max] fails fast
    # rather than looping on an empty operand list.
    with pytest.raises(ValueError):
        tex_module.generate_ope_problems(
            list(range(1, 10)), list(range(1, 10)), ['add'],
            order=1, start_index=1, **multiple_kwargs,
        )


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


def test_calc_div_remainder_true_returns_nonzero_remainder() -> None:
    nums_a = list(range(10, 100))
    nums_b = list(range(2, 10))
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_div(50, 3, nums_a, nums_b, remainder=True)
        assert b != 0
        assert a % b != 0
        assert c == a // b


def test_calc_div_remainder_false_matches_default_exact_behavior() -> None:
    nums_a = list(range(10, 100))
    nums_b = list(range(1, 10))
    a, b, c = tex_module.calc_div(50, 3, nums_a, nums_b, remainder=False)
    assert a % b == 0
    assert c == a // b


def test_calc_div_remainder_true_succeeds_when_valid_pair_space_is_narrow(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)
    a, b, c = tex_module.calc_div(10, 3, [10], [3], remainder=True)
    assert a % b != 0
    assert c == a // b


def test_calc_div_remainder_true_raises_when_no_remainder_pair_is_possible() -> None:
    with pytest.raises(ValueError):
        tex_module.calc_div(2, 1, [2, 4], [1], remainder=True)


def test_find_remainder_division_pair_returns_none_when_impossible() -> None:
    assert tex_module.find_remainder_division_pair([2, 4], [1]) is None


def test_calc_div_quotient_digits_restricts_quotient_width() -> None:
    nums_a = list(range(20, 100))
    nums_b = list(range(2, 10))
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_div(20, 2, nums_a, nums_b, quotient_digits=2)
        assert a % b == 0
        assert c == a // b
        assert 10 <= c <= 99


def test_calc_div_quotient_digits_combines_with_remainder() -> None:
    nums_a = list(range(20, 100))
    nums_b = list(range(2, 10))
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c = tex_module.calc_div(20, 3, nums_a, nums_b, remainder=True, quotient_digits=2)
        assert a % b != 0
        assert c == a // b
        assert 10 <= c <= 99


def test_calc_div_quotient_digits_uses_deterministic_fallback(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    # 96 / 8 = 12 is the only exact pair in these ranges (50 % 8 != 0), and
    # its quotient is 2-digit, so the deterministic fallback must return it.
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)
    a, b, c = tex_module.calc_div(50, 8, [50, 96], [8], quotient_digits=2)
    assert (a, b, c) == (96, 8, 12)


def test_calc_div_quotient_digits_raises_when_impossible() -> None:
    with pytest.raises(ValueError):
        tex_module.calc_div(8, 4, [8], [4], quotient_digits=2)


def test_find_exact_division_pair_honors_quotient_digits() -> None:
    pair = tex_module.find_exact_division_pair(list(range(20, 100)), list(range(2, 10)), 2)
    assert pair is not None
    a, b = pair
    assert a % b == 0
    assert 10 <= a // b <= 99
    assert tex_module.find_exact_division_pair([8], [4], 2) is None


def test_find_remainder_division_pair_honors_quotient_digits() -> None:
    pair = tex_module.find_remainder_division_pair(list(range(20, 100)), list(range(2, 10)), 2)
    assert pair is not None
    a, b = pair
    assert a % b != 0
    assert 10 <= a // b <= 99
    assert tex_module.find_remainder_division_pair([7], [3], 2) is None


@pytest.mark.parametrize(
    ("remainder_mode", "expect_remainder"),
    [('required', True), ('none', False)],
)
def test_generate_ope_problems_applies_division_remainder_filter(
        remainder_mode: tex_module.RemainderMode, expect_remainder: bool,
    ) -> None:
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(2, 10)), ['div'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, remainder_mode=remainder_mode,
    )

    assert all((problem.remainder != 0) is expect_remainder for problem in problems)
    assert all(problem.remainder == problem.a - problem.b * problem.c for problem in problems)


def test_generate_ope_problems_mixed_remainder_covers_both_conditions() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(2, 10)), ['div'],
        order=2000, start_index=1, remainder_mode='mixed',
    )

    observed = {problem.remainder != 0 for problem in problems}
    assert observed == {False, True}
    for problem in problems:
        assert problem.remainder == problem.a - problem.b * problem.c


def test_generate_ope_problems_default_remainder_mode_is_always_exact() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(10, 100)), list(range(1, 10)), ['div'],
        order=GENERATION_SAMPLE_SIZE, start_index=1,
    )
    assert all(problem.remainder == 0 for problem in problems)


def test_generate_ope_problems_quotient_digits_forces_two_digit_quotient() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(20, 100)), list(range(2, 10)), ['div'],
        order=GENERATION_SAMPLE_SIZE, start_index=1, quotient_digits=2,
    )
    assert len(problems) == GENERATION_SAMPLE_SIZE
    for problem in problems:
        assert problem.operator == 'div'
        assert problem.remainder == 0
        assert problem.a % problem.b == 0
        assert 10 <= problem.c <= 99


def test_generate_ope_problems_quotient_digits_combines_with_mixed_remainder() -> None:
    problems = tex_module.generate_ope_problems(
        list(range(20, 100)), list(range(2, 10)), ['div'],
        order=2000, start_index=1, remainder_mode='mixed', quotient_digits=2,
    )
    observed = {problem.remainder != 0 for problem in problems}
    assert observed == {False, True}
    for problem in problems:
        assert 10 <= problem.c <= 99
        assert problem.remainder == problem.a - problem.b * problem.c


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
    assert '= \\opspace 5}' not in blank_tex
    assert '\\underline' not in blank_tex
    assert '2 \\opspace + \\opspace 3' in blank_tex
    assert blank_tex == (
        '1) \\horizontaleq{2 \\opspace + \\opspace 3 \\opspace = \\opspace \\hspace{1.5em}}'
    )
    assert filled_tex == (
        '1) \\horizontaleq{2 \\opspace + \\opspace 3 \\opspace = \\opspace 5}'
    )


def test_build_horizontal_block_tex_div_without_remainder_is_unchanged() -> None:
    problem = tex_module.OpeProblem(index=1, a=6, b=3, operator='div', c=2)
    filled_tex = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    assert 'あまり' not in filled_tex
    assert filled_tex == (
        '1) \\horizontaleq{6 \\opspace \\div \\opspace 3 \\opspace = \\opspace 2}'
    )


def test_build_horizontal_block_tex_div_with_remainder_shows_cdots_and_blanks_it() -> None:
    problem = tex_module.OpeProblem(index=1, a=17, b=5, operator='div', c=3, remainder=2)
    blank_tex = tex_module.build_horizontal_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    assert blank_tex == (
        '1) \\horizontaleq{17 \\opspace \\div \\opspace 5 \\opspace = \\opspace '
        '\\hspace{1.5em} \\cdots \\hspace{1.5em}}'
    )
    assert '2' not in blank_tex
    assert filled_tex == (
        '1) \\horizontaleq{17 \\opspace \\div \\opspace 5 \\opspace = \\opspace 3 \\cdots 2}'
    )


def test_build_horizontal_intermediate_block_tex_blank_hides_answer_without_underline() -> None:
    problem = tex_module.OpeProblem(index=1, a=23, b=4, operator='mul', c=92)
    blank_tex = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_horizontal_intermediate_block_tex(problem, show_answer=True)
    assert '92' not in blank_tex
    assert '\\underline' not in blank_tex
    # issue #268: emitted via the shared staged arrow-chain components -- the
    # \times carries the centralized \opspace gap, the memo goes in a
    # fixed-width \stagechainmemo box, and \stagechainarrow separates the stages.
    assert blank_tex == (
        '1) \\stagedchaineq{23 \\opspace \\times \\opspace 4 \\stagechainarrow '
        '\\stagechainmemo{0812} \\stagechainarrow \\hspace{1.5em}}'
    )
    assert filled_tex == (
        '1) \\stagedchaineq{23 \\opspace \\times \\opspace 4 \\stagechainarrow '
        '\\stagechainmemo{0812} \\stagechainarrow 92}'
    )


def test_build_vertical_block_tex_div_uses_stage_zero_for_blank() -> None:
    problem = tex_module.OpeProblem(index=1, a=100, b=10, operator='div', c=10)
    blank_tex = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_vertical_block_tex(problem, show_answer=True)
    # issue #269: div is emitted via the shared \longdivisioncalc /
    # \longdivisioncalcblank wrappers; the blank one keeps longdivision's
    # built-in stage=0 blanking (the [stage=0] option now lives inside the
    # \longdivisioncalcblank macro body -- see build_content_format_macros_tex
    # and test_nuts_calc_tex_written_calculation_content_format.py).
    assert '\\longdivisioncalcblank{100}{10}' in blank_tex
    assert '\\longdivisioncalcblank' not in filled_tex
    assert '\\longdivisioncalc{100}{10}' in filled_tex
    macros = tex_module.build_content_format_macros_tex()
    assert (
        '\\newcommand{\\longdivisioncalcblank}[2]{\\problemfractionstyle{\\hissandigitfont'
        '$\\intlongdivision[stage=0]{#1}{#2}$}}' in macros
    )
    assert (
        '\\newcommand{\\longdivisioncalc}[2]{\\problemfractionstyle{\\hissandigitfont'
        '$\\intlongdivision{#1}{#2}$}}' in macros
    )


def test_build_vertical_block_tex_positions_operator_one_digit_left_of_numbers() -> None:
    problem = tex_module.OpeProblem(index=1, a=23, b=4, operator='add', c=27)
    blank_tex = tex_module.build_vertical_block_tex(problem, show_answer=False)
    filled_tex = tex_module.build_vertical_block_tex(problem, show_answer=True)

    # issue #269: add/sub/mul are emitted via the shared \verticalcalc /
    # \verticalcalcblank wrappers, which apply the centralized \verticalcalcsetup
    # \opset group (voperator=bottom + columnwidth=\verticalcolumnwidth) instead
    # of an inline magic option string. The blank wrapper layers the per-digit
    # \phantom style hooks; the filled one does not.
    assert filled_tex == '1)\\newline \\verticalcalc{\\opadd{23}{4}}'
    assert blank_tex == '1)\\newline \\verticalcalcblank{\\opadd{23}{4}}'
    assert 'resultstyle=\\phantom' not in filled_tex


def test_build_ope_csv_rows_has_one_row_per_problem() -> None:
    page1 = [tex_module.OpeProblem(index=1, a=2, b=3, operator='add', c=5)]
    page2 = [tex_module.OpeProblem(index=2, a=9, b=4, operator='sub', c=5)]
    rows = tex_module.build_ope_csv_rows([page1, page2])
    assert rows == [
        [1, 1, 2, 'add', 3, 5, 0],
        [2, 2, 9, 'sub', 4, 5, 0],
    ]


def test_build_ope_csv_rows_includes_remainder_column_for_div() -> None:
    page = [tex_module.OpeProblem(index=1, a=17, b=5, operator='div', c=3, remainder=2)]
    rows = tex_module.build_ope_csv_rows([page])
    assert rows == [[1, 1, 17, 'div', 5, 3, 2]]


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
    assert tex_module.build_tree_ope_expression_tex(tree) == (
        '3 \\opspace + \\opspace (5 \\opspace \\times \\opspace 2)'
    )
    assert tex_module.build_tree_ope_structure_text(tree) == '3 add (5 mul 2)'


def test_generate_tree_ope_problems_assigns_sequential_indices() -> None:
    problems = tex_module.generate_tree_ope_problems(
        [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3, order=4, start_index=11,
    )
    assert [problem.index for problem in problems] == [11, 12, 13, 14]
    # All leaves are 5 (first) or 3 (rest) with only 'add', so every shape
    # sums to 5 + 3 + 3 == 11 regardless of tree structure.
    assert [problem.result for problem in problems] == [11] * 4


def test_generate_tree_ope_problems_applies_result_max() -> None:
    problems = tex_module.generate_tree_ope_problems(
        [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3,
        order=2, start_index=1, result_max=11,
    )

    assert [problem.result for problem in problems] == [11, 11]


def test_generate_tree_ope_problems_rejects_impossible_result_max() -> None:
    with pytest.raises(ValueError):
        tex_module.generate_tree_ope_problems(
            [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3,
            order=1, start_index=1, result_max=10,
        )


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


# --- nontrivial_division (issue #342) -------------------------------------

# The frontend g4-parentheses preset's generator inputs: single-digit
# operands, 3-leaf trees, all four operators, per-node operator mixing.
G4_PARENTHESES_NUMS = list(range(1, 10))
NONTRIVIAL_DIVISION_SAMPLE_SIZE = 300


def _collect_div_operator_nodes(node: "tex_module.ExprTreeNode") -> list["tex_module.ExprTreeNode"]:
    """Every division node in `node` (for asserting nontrivial_division invariants)."""
    if node.is_leaf:
        return []
    found = _collect_div_operator_nodes(node.left) + _collect_div_operator_nodes(node.right)
    return found + [node] if node.operator == 'div' else found


def test_tree_has_only_nontrivial_divisions_rejects_trivial_and_missing_divisions() -> None:
    leaf = tex_module.ExprTreeNode

    div_by_one = tex_module.ExprTreeNode(operator='div', left=leaf(value=8), right=leaf(value=1))
    tex_module.evaluate_expr_tree(div_by_one)
    assert tex_module.tree_has_only_nontrivial_divisions(div_by_one) is False

    div_by_self = tex_module.ExprTreeNode(operator='div', left=leaf(value=6), right=leaf(value=6))
    tex_module.evaluate_expr_tree(div_by_self)
    assert tex_module.tree_has_only_nontrivial_divisions(div_by_self) is False

    no_div = tex_module.ExprTreeNode(operator='add', left=leaf(value=3), right=leaf(value=5))
    tex_module.evaluate_expr_tree(no_div)
    assert tex_module.tree_has_only_nontrivial_divisions(no_div) is False

    # (8 + 4) / 3 = 4 -> divisor 3, quotient 4: genuine.
    genuine = tex_module.ExprTreeNode(
        operator='div',
        left=tex_module.ExprTreeNode(operator='add', left=leaf(value=8), right=leaf(value=4)),
        right=leaf(value=3),
    )
    tex_module.evaluate_expr_tree(genuine)
    assert tex_module.tree_has_only_nontrivial_divisions(genuine) is True

    # One genuine div node and one trivial (/1) div node -> whole tree rejected.
    mixed_trivial = tex_module.ExprTreeNode(
        operator='div',
        left=tex_module.ExprTreeNode(operator='div', left=leaf(value=8), right=leaf(value=4)),
        right=leaf(value=1),
    )
    tex_module.evaluate_expr_tree(mixed_trivial)
    assert tex_module.tree_has_only_nontrivial_divisions(mixed_trivial) is False


def test_generate_tree_ope_problems_nontrivial_division_guarantees_a_division() -> None:
    problems = tex_module.generate_tree_ope_problems(
        G4_PARENTHESES_NUMS, G4_PARENTHESES_NUMS, ['add', 'sub', 'mul', 'div'], mixed=True,
        terms_min=3, terms_max=3, order=NONTRIVIAL_DIVISION_SAMPLE_SIZE, start_index=1,
        nontrivial_division=True,
    )
    # A full sample with no ValueError also proves the stricter filter
    # converges well within MAX_OPERAND_RETRY_ATTEMPTS for this config.
    assert len(problems) == NONTRIVIAL_DIVISION_SAMPLE_SIZE
    for problem in problems:
        assert 'div' in problem.operators


def test_generate_tree_ope_problems_nontrivial_division_rejects_trivial_divisions() -> None:
    problems = tex_module.generate_tree_ope_problems(
        G4_PARENTHESES_NUMS, G4_PARENTHESES_NUMS, ['add', 'sub', 'mul', 'div'], mixed=True,
        terms_min=3, terms_max=3, order=NONTRIVIAL_DIVISION_SAMPLE_SIZE, start_index=1,
        nontrivial_division=True,
    )
    for problem in problems:
        div_nodes = _collect_div_operator_nodes(problem.tree)
        assert div_nodes, f"expected a division node in {problem.operators}"
        for node in div_nodes:
            assert node.right.value >= tex_module.NONTRIVIAL_DIVISOR_MIN
            assert node.left.value // node.right.value >= tex_module.NONTRIVIAL_QUOTIENT_MIN


def test_generate_tree_ope_problems_nontrivial_division_is_noop_without_mixed() -> None:
    # With a single shared operator the flag must not become a div-only
    # filter (shared 'add' would then exhaust the retry budget).
    problems = tex_module.generate_tree_ope_problems(
        [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3,
        order=4, start_index=1, nontrivial_division=True,
    )
    assert [problem.result for problem in problems] == [11] * 4


def test_generate_tree_ope_problems_nontrivial_division_is_noop_without_div_operator() -> None:
    problems = tex_module.generate_tree_ope_problems(
        G4_PARENTHESES_NUMS, G4_PARENTHESES_NUMS, ['add', 'mul'], mixed=True,
        terms_min=3, terms_max=3, order=GENERATION_SAMPLE_SIZE, start_index=1,
        nontrivial_division=True,
    )
    assert len(problems) == GENERATION_SAMPLE_SIZE
    for problem in problems:
        assert set(problem.operators) <= {'add', 'mul'}


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


def test_generate_multi_term_ope_problems_applies_result_max() -> None:
    problems = tex_module.generate_multi_term_ope_problems(
        [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3,
        order=2, start_index=1, result_max=11,
    )

    assert [problem.result for problem in problems] == [11, 11]


def test_generate_multi_term_ope_problems_rejects_impossible_result_max() -> None:
    with pytest.raises(ValueError):
        tex_module.generate_multi_term_ope_problems(
            [5], [3], ['add'], mixed=False, terms_min=3, terms_max=3,
            order=1, start_index=1, result_max=10,
        )


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
    expression_tex = filled_tex.split('\\horizontaleq{', 1)[1]
    assert '(' not in expression_tex and ')' not in expression_tex
    assert blank_tex == (
        '1) \\horizontaleq{5 \\opspace + \\opspace 3 \\opspace - \\opspace 2 '
        '\\opspace = \\opspace \\hspace{1.5em}}'
    )
    assert filled_tex == (
        '1) \\horizontaleq{5 \\opspace + \\opspace 3 \\opspace - \\opspace 2 '
        '\\opspace = \\opspace 6}'
    )


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


def test_generate_missing_value_problems_applies_result_max() -> None:
    problems = tex_module.generate_missing_value_problems(
        [999], [1], ['add'], order=2, start_index=1, result_max=1000,
    )

    assert [problem.c for problem in problems] == [1000, 1000]


def test_generate_missing_value_problems_rejects_impossible_result_max() -> None:
    with pytest.raises(ValueError, match="satisfies --result-max"):
        tex_module.generate_missing_value_problems(
            [999], [2], ['add'], order=1, start_index=1, result_max=1000,
        )


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

    # Pattern 2 now emits via the shared \boxedblankeq / \opspace / \boxedblank
    # components (issue #265) instead of a raw $...$ f-string.
    assert blank_tex == (
        "1) \\boxedblankeq{2 \\opspace + \\opspace "
        f"{tex_module.BOXED_BLANK_OPERAND_TEX} \\opspace = \\opspace 5}}"
    )
    assert filled_tex == "1) \\boxedblankeq{2 \\opspace + \\opspace 3 \\opspace = \\opspace 5}"


def test_build_missing_value_block_tex_boxes_a_when_blank_is_a() -> None:
    problem = tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='a')
    blank_tex = tex_module.build_missing_value_block_tex(problem, show_answer=False)
    assert blank_tex == (
        "1) \\boxedblankeq{"
        f"{tex_module.BOXED_BLANK_OPERAND_TEX} \\opspace + \\opspace 3 \\opspace = \\opspace 5}}"
    )


def test_build_missing_value_block_tex_always_shows_the_result() -> None:
    problem = tex_module.MissingValueProblem(index=1, a=2, b=3, operator='add', c=5, blank='a')
    blank_tex = tex_module.build_missing_value_block_tex(problem, show_answer=False)
    assert '\\opspace = \\opspace 5}' in blank_tex
    assert tex_module.BOXED_BLANK_OPERAND_TEX not in blank_tex.split('=')[-1]


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
