"""Unit tests for nuts_calc.py's problem-data generation functions.

These exercise the pure(ish) data-generation helpers directly (no PDF
rendering, no subprocess), so they run fast and pin exact arithmetic.
Comments reference GitHub issue #4 where a test's inputs are specifically
chosen to avoid a since-fixed logic bug (e.g. picking operand ranges that
can't hit the calc_sub/calc_div retry-loop bug from Phase 5).
"""

import nuts_calc as nc


# ---------------------------------------------------------------------------
# pad_digits_to_width / get_vertical_digit_width
# ---------------------------------------------------------------------------


def test_pad_digits_to_width_right_aligns_and_blanks_leading_cells():
    assert nc.pad_digits_to_width("45", 4) == ["", "", "4", "5"]


def test_pad_digits_to_width_exact_width_has_no_blanks():
    assert nc.pad_digits_to_width("7", 1) == ["7"]


def test_get_vertical_digit_width_for_add_uses_sum_of_max_operands():
    assert nc.get_vertical_digit_width(9, 9, ["add"]) == 2  # 9+9=18


def test_get_vertical_digit_width_for_sub_uses_max_operand():
    assert nc.get_vertical_digit_width(9, 9, ["sub"]) == 1


def test_get_vertical_digit_width_for_mul_uses_product_of_max_operands():
    assert nc.get_vertical_digit_width(9, 9, ["mul"]) == 2  # 9*9=81


def test_get_vertical_digit_width_takes_max_across_operators():
    assert nc.get_vertical_digit_width(9, 9, ["add", "mul"]) == 2


def test_get_vertical_digit_width_for_multi_digit_mul_uses_product_of_max_operands():
    assert nc.get_vertical_digit_width(999, 99, ["mul"]) == 5  # 999*99=98901


# ---------------------------------------------------------------------------
# get_mul_partial_products (multi-digit multiplier, written multiplication)
# ---------------------------------------------------------------------------


def test_get_mul_partial_products_single_digit_multiplier_returns_one_value():
    assert nc.get_mul_partial_products("7", "3") == ["21"]


def test_get_mul_partial_products_multi_digit_multiplier_orders_ones_digit_first():
    # 123 x 45: ones-digit partial (123*5) first, then tens-digit partial (123*4).
    assert nc.get_mul_partial_products("123", "45") == ["615", "492"]


def test_get_mul_partial_products_returns_one_partial_per_digit_of_multiplier():
    assert nc.get_mul_partial_products("7", "234") == ["28", "21", "14"]


# ---------------------------------------------------------------------------
# compute_long_division_layout (vertical long division, issue #11)
# ---------------------------------------------------------------------------


def test_compute_long_division_layout_single_digit_divisor():
    # 84 / 7 = 12: each dividend digit starts its own step (no leading-zero skip).
    quotient_cells, rows = nc.compute_long_division_layout(84, 7)
    assert quotient_cells == ["1", "2"]
    assert rows == [
        ("product", 0, "7"),
        ("partial", 1, "14"),
        ("product", 1, "14"),
        ("remainder", 1, "0"),
    ]


def test_compute_long_division_layout_leading_zero_skip():
    # 120 / 30 = 4: first two digits (1, 2) fold into the remainder with a
    # zero quotient digit each (suppressed/blank) before the first nonzero
    # quotient digit appears at the last position, consuming all 3 digits
    # at once -- so no 'partial' row is emitted (the dividend row already
    # shows all 3 digits).
    quotient_cells, rows = nc.compute_long_division_layout(120, 30)
    assert quotient_cells == ["", "", "4"]
    assert rows == [
        ("product", 2, "120"),
        ("remainder", 2, "0"),
    ]


def test_compute_long_division_layout_multi_digit_divisor():
    # 875 / 25 = 35, matching the g4-div preset's digit range (3-digit
    # dividend / 2-digit divisor).
    quotient_cells, rows = nc.compute_long_division_layout(875, 25)
    assert quotient_cells == ["", "3", "5"]
    assert rows == [
        ("product", 1, "75"),
        ("partial", 2, "125"),
        ("product", 2, "125"),
        ("remainder", 2, "0"),
    ]


def test_compute_long_division_layout_remainder_is_always_zero_for_exact_division():
    # calc_div only pairs evenly-divisible operands, so the final remainder
    # row is always "0" for any exact-division input.
    _, rows = nc.compute_long_division_layout(144, 12)
    assert rows[-1][0] == "remainder"
    assert rows[-1][2] == "0"


# ---------------------------------------------------------------------------
# get_operation_data
# ---------------------------------------------------------------------------


def test_get_operation_data_add_returns_correct_sums_and_indices():
    order = 20
    data = nc.get_operation_data([2, 3, 4], [5, 6], operators=["add"], order=order, print_index=1)
    data_index, vals_a, operator_mark, vals_b, equal_marks, vals_c = data

    assert len(data_index) == order
    for i in range(order):
        a, b, c = int(vals_a[i][0]), int(vals_b[i][0]), int(vals_c[i][0])
        assert a + b == c
        assert operator_mark[i][0] == "+"
        assert equal_marks[i][0] == "="
        assert data_index[i][0] == f"{i + 1})"


def test_get_operation_data_sub_never_negative():
    # nums_a all larger than any nums_b, so a - b > 0 always holds immediately
    # (no retry loop needed, avoiding the infinite-loop risk in calc_sub --
    # see issue #4 Phase 5).
    data = nc.get_operation_data([10, 20, 30], [1, 2, 3], operators=["sub"], order=15, print_index=1)
    _, vals_a, operator_mark, vals_b, _, vals_c = data
    for i in range(15):
        a, b, c = int(vals_a[i][0]), int(vals_b[i][0]), int(vals_c[i][0])
        assert a - b == c
        assert c > 0
        assert operator_mark[i][0] == "-"


def test_get_operation_data_mul_returns_correct_products():
    data = nc.get_operation_data([2, 3, 4], [5, 6, 7], operators=["mul"], order=10, print_index=1)
    _, vals_a, operator_mark, vals_b, _, vals_c = data
    for i in range(10):
        a, b, c = int(vals_a[i][0]), int(vals_b[i][0]), int(vals_c[i][0])
        assert a * b == c
        assert operator_mark[i][0] == "×"


def test_get_operation_data_div_always_exact():
    # nums_a all even, nums_b=[2] so every pair divides exactly on the first
    # try (no retry loop needed -- see issue #4 Phase 5).
    data = nc.get_operation_data([6, 8, 10], [2], operators=["div"], order=10, print_index=1)
    _, vals_a, operator_mark, vals_b, _, vals_c = data
    for i in range(10):
        a, b, c = int(vals_a[i][0]), int(vals_b[i][0]), int(vals_c[i][0])
        assert a % b == 0
        assert a // b == c
        assert operator_mark[i][0] == "÷"


def test_get_operation_data_mix_only_uses_the_four_base_operators():
    # a=8 fixed, b in {1,2,4}: sub (8-b>0) and div (8%b==0) always succeed
    # immediately for every operator drawn from the mix expansion, so no
    # operator can hit the calc_sub/calc_div retry loop (issue #4 Phase 5).
    data = nc.get_operation_data([8], [1, 2, 4], operators=["mix"], order=30, print_index=1)
    _, _, operator_mark, _, _, _ = data
    seen = {row[0] for row in operator_mark}
    assert seen <= {"+", "-", "×", "÷"}


def test_get_operation_data_intermediate_matches_memo_mental_arithmetic_technique():
    # get_operation_data's "aabb" intermediate implements the 2-digit x 1-digit
    # mental-arithmetic technique documented in memo.md (STEP 1: build a 4-digit
    # number from tens(a)*b and ones(a)*b, zero-padded to 2 digits each and
    # concatenated). This is only valid for a single-digit b (issue #4 Phase 3:
    # nuts_calc.py's _init() now rejects --intermediate with a 2-digit b at the
    # CLI level -- see tests/test_nuts_calc_init.py).
    #
    # Single-element nums_a/nums_b make the draw deterministic. memo.md's own
    # worked example: 32 x 6 -> 1812 -> 192.
    data = nc.get_operation_data([32], [6], operators=["mul"], order=1, print_index=1, intermediate=True)
    data_index, vals_a, operator_mark, vals_b, arrow1, vals_aabb, arrow2, vals_c = data

    assert vals_a[0][0] == "32"
    assert vals_b[0][0] == "6"
    assert vals_aabb[0][0] == "1812"
    assert vals_c[0][0] == "192"
    assert arrow1[0][0] == "=>"
    assert arrow2[0][0] == "=>"

    # STEP 2 (done mentally by the student): first two digits + third digit,
    # then append the fourth digit. This must always reproduce a * b exactly.
    d1, d2, d3, d4 = (int(ch) for ch in vals_aabb[0][0])
    step2_result = (d1 * 10 + d2 + d3) * 10 + d4
    assert step2_result == int(vals_c[0][0])


# ---------------------------------------------------------------------------
# get_complement_data
# ---------------------------------------------------------------------------


def test_get_complement_data_sums_to_target():
    target = 100
    order = 12
    data = nc.get_complement_data([10, 20, 30], target=target, order=order, print_index=1)
    data_index, vals_a, equal_marks, vals_c = data

    assert len(data_index) == order
    for i in range(order):
        # get_complement_data stores raw ints, unlike get_operation_data's strings.
        assert vals_a[i][0] + vals_c[i][0] == target
        assert equal_marks[i][0] == "=>"
        assert data_index[i][0] == f"{i + 1})"


# ---------------------------------------------------------------------------
# get_fixed_format_data
# ---------------------------------------------------------------------------


def test_get_fixed_format_data_99_multiplies_fixed_a_by_increasing_b():
    order = 9
    data = nc.get_fixed_format_data("99", start_num=3, order=order, print_index=1)
    data_index, vals_a, operator_marks, vals_b, equal_marks, vals_c = data

    for i in range(order):
        assert vals_a[i][0] == 3
        assert vals_b[i][0] == i + 1
        assert vals_c[i][0] == 3 * (i + 1)
        assert operator_marks[i][0] == "×"
        assert equal_marks[i][0] == "="


def test_get_fixed_format_data_squ_squares_sequential_numbers():
    data = nc.get_fixed_format_data("squ", start_num=1, order=5, print_index=1)
    _, vals_a, _, vals_b, _, vals_c = data
    for i in range(5):
        a = i + 1
        assert vals_a[i][0] == a
        assert vals_b[i][0] == a
        assert vals_c[i][0] == a * a


def test_get_fixed_format_data_pi_multiplies_by_314():
    data = nc.get_fixed_format_data("pi", start_num=1, order=3, print_index=1)
    _, vals_a, _, vals_b, _, vals_c = data
    for i in range(3):
        a = i + 1
        assert vals_b[i][0] == 3.14
        assert vals_c[i][0] == a * 3.14


def test_get_fixed_format_data_descend_reverses_sequence_order():
    normal = nc.get_fixed_format_data("squ", start_num=1, order=5, print_index=1)
    descend = nc.get_fixed_format_data("squ", start_num=1, order=5, print_index=1, descend=True)
    normal_a = [row[0] for row in normal[1]]
    descend_a = [row[0] for row in descend[1]]
    assert descend_a == list(reversed(normal_a))


def test_get_fixed_format_data_shuffle_keeps_same_value_set():
    data = nc.get_fixed_format_data("squ", start_num=1, order=10, print_index=1, is_shuffle=True)
    vals_a = sorted(row[0] for row in data[1])
    assert vals_a == list(range(1, 11))


def test_get_fixed_format_data_reverse_flag_swaps_operand_and_result_columns():
    normal = nc.get_fixed_format_data("squ", start_num=1, order=5, print_index=1)
    reversed_ = nc.get_fixed_format_data("squ", start_num=1, order=5, print_index=1, is_reverse=True)
    # normal   = (data_index, vals_a, operator_marks, vals_b, equal_marks, vals_c)
    # reversed = (data_index, vals_c, equal_marks, vals_a, operator_marks, vals_b)
    assert reversed_[1] == normal[5]
    assert reversed_[3] == normal[1]


# ---------------------------------------------------------------------------
# get_aBc_data
# ---------------------------------------------------------------------------


def test_get_aBc_data_a_d_matches_recomputed_value_from_digits():
    # get_aBc_data only zero-pads its stored abcd string when the value is
    # exactly 3 digits (a==0, b>=1); for a==0 and b==0 the stored string can
    # be shorter than 4 characters. To avoid a flaky test tied to that
    # separate quirk, digits are recovered from the *value* (zero-filled to
    # 4 here in the test), not from the stored string's own length.
    order = 30
    data = nc.get_aBc_data(order=order, print_index=1)
    data_index, vals_a, equal_marks, vals_c = data

    assert len(data_index) == order
    for i in range(order):
        value = int(vals_a[i][0])
        a, b, c, d = (int(ch) for ch in str(value).zfill(4))
        ab = (a * 10 + b) * 10
        cd = c * 10 + d
        assert int(vals_c[i][0]) == ab + cd
        assert equal_marks[i][0] == "=>"
        assert data_index[i][0] == f"{i + 1})"
