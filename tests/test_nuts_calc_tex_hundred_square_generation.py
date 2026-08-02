"""Unit tests for nuts_calc_tex.py's `100` problem-generation logic (issue #23).

These exercise the pure-Python generation/rendering-data functions directly
(no pdflatex required), complementing the pdflatex-gated end-to-end tests in
test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import nuts_calc_tex as tex_module  # noqa: E402

GENERATION_SAMPLE_ROUNDS = 50


def test_sample_hundred_square_values_returns_required_count_for_default_range() -> None:
    # Default digit-1 range (1-9) has only 9 distinct values for 10 slots,
    # so the doubled-seed sampling must still succeed without raising.
    nums = list(range(1, 10))
    values = tex_module.sample_hundred_square_values(nums)
    assert len(values) == tex_module.HUNDRED_SQUARE_SIZE
    assert set(values) <= set(nums)


def test_sample_hundred_square_values_repeats_at_most_twice() -> None:
    nums = list(range(1, 10))
    for _ in range(GENERATION_SAMPLE_ROUNDS):
        values = tex_module.sample_hundred_square_values(nums)
        for value in set(values):
            assert values.count(value) <= tex_module.HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR


def test_generate_hundred_square_answers_equal_left_plus_top() -> None:
    table = tex_module.generate_hundred_square(list(range(1, 10)), list(range(10, 100)))
    assert len(table.left_values) == tex_module.HUNDRED_SQUARE_SIZE
    assert len(table.top_values) == tex_module.HUNDRED_SQUARE_SIZE
    for row_index, left in enumerate(table.left_values):
        for col_index, top in enumerate(table.top_values):
            assert table.answers[row_index][col_index] == left + top


def test_build_hundred_square_block_tex_blank_hides_answers() -> None:
    table = tex_module.HundredSquareTable(
        left_values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 1],
        top_values=[10, 20, 30, 40, 50, 60, 70, 80, 90, 15],
    )
    blank_tex = tex_module.build_hundred_square_block_tex(table, show_answer=False)
    filled_tex = tex_module.build_hundred_square_block_tex(table, show_answer=True)

    assert '11' not in blank_tex  # 1 + 10
    assert '11' in filled_tex
    assert '\\rowcolor{lightgray}' in blank_tex
    assert '\\columncolor{lightgray}' in blank_tex
    # header row/column values are shown in both variants
    assert '10' in blank_tex and '10' in filled_tex


def test_build_hundred_square_csv_rows_has_header_and_data_rows_per_page() -> None:
    # Only exercises the shape/semantics of the CSV rows, not the full
    # 10x10 default table size.
    table = tex_module.HundredSquareTable(
        left_values=[1, 2],
        top_values=[10, 20],
    )
    rows = tex_module.build_hundred_square_csv_rows([table])

    assert rows[0] == [1, '', 10, 20]
    assert rows[1] == [1, 1, 11, 21]
    assert rows[2] == [1, 2, 12, 22]
