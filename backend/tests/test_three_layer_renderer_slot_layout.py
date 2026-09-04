"""Tests for `three_layer_renderer._resolve_number_placement` (issue #355).

`_resolve_number_placement` picks the Layer 2 inline-slot number placement
from the `/generate-pdf` request dict: an alternate placement for a 1-2
column grid of short single-line drills so the columns are not lopsided to
the left, and the default ``gutter`` for everything else. The allowlist is
deliberately conservative, so every non-allowlisted command type and every
`ope` variant keeps byte-identical output.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402


ALT = three_layer_renderer._SHORT_DRILL_NUMBER_PLACEMENT
GUTTER = nuts_calc_tex.DEFAULT_NUMBER_PLACEMENT


def test_the_alternate_placement_is_a_valid_non_default_number_placement() -> None:
    assert ALT != GUTTER
    assert ALT in ("gutter", "gutter-centered", "inline")


@pytest.mark.parametrize(
    "data",
    [
        {'command_type': '99'},
        {'command_type': 'squ'},
        {'command_type': 'pi'},
        {'command_type': 'com', 'a_value': 10},
        {'command_type': 'evenodd'},
        {'command_type': 'lcm'},
        {'command_type': 'gcd'},
        {'command_type': '99', 'columns': 2},
        {'command_type': 'ope', 'operator': ['add'], 'a_max': 99, 'b_max': 99},
        {'command_type': 'ope', 'operator': ['sub'], 'a_digits': 2, 'b_digits': 1},
        {'command_type': 'ope'},
        {'command_type': 'ope', 'operator': ['mul'], 'a_max': 9, 'b_max': 9, 'columns': 2},
        # grade-3 3-digit x 1-/2-digit multiplication: still one short line
        {'command_type': 'ope', 'operator': ['mul'], 'a_min': 100, 'a_max': 999, 'b_min': 1, 'b_max': 9},
        {'command_type': 'ope', 'operator': ['mul'], 'a_digits': 3, 'b_digits': 2},
        {'command_type': 'ope', 'operator': ['add'], 'a_max': 999, 'b_max': 99},
        # decimals / division-with-remainder / add-sub operator mix are still
        # one short line per row
        {'command_type': 'ope', 'operator': ['add'], 'a_decimal_places': 1, 'b_decimal_places': 1},
        {'command_type': 'ope', 'operator': ['div'], 'remainder_mode': 'required'},
        {'command_type': 'ope', 'operator': ['add', 'sub']},
        # a `review` worksheet whose every source is a plain two-term ope
        # equation (grade-1 g1-review, issue #365)
        {'command_type': 'review', 'sources': [{'command_type': 'ope', 'num': 1}]},
        {
            'command_type': 'review',
            'sources': [
                {'command_type': 'ope', 'num': 1, 'operator': ['add'], 'carry_mode': 'required'},
                {'command_type': 'ope', 'num': 1, 'operator': ['add', 'sub'],
                 'a_multiple': 10, 'b_multiple': 10},
                {'command_type': 'evenodd', 'num': 1},
            ],
        },
    ],
)
def test_short_single_line_drills_get_the_alternate_placement(data) -> None:
    assert three_layer_renderer._resolve_number_placement(data) == ALT


@pytest.mark.parametrize(
    "data",
    [
        # non-allowlisted command types keep gutter (byte-identical output)
        {'command_type': 'frac', 'operator': ['add']},
        {'command_type': 'mixed'},
        {'command_type': 'compare'},
        {'command_type': '100'},
        {'command_type': 'divfrac'},
        {'command_type': 'approx', 'kind': 'round'},
        {'command_type': 'multiples'},
        {'command_type': 'divisors'},
        {'command_type': 'aBc'},
        # a `review` worksheet keeps the gutter as soon as one source is wide:
        # a fraction (grade-3 g3-review), a multi-term chain, or a vertical
        # hissan -- and an empty / malformed sources list is not short either
        {'command_type': 'review', 'sources': [
            {'command_type': 'ope', 'num': 1}, {'command_type': 'frac', 'num': 1}]},
        {'command_type': 'review', 'sources': [{'command_type': 'ope', 'num': 1, 'terms': 3}]},
        {'command_type': 'review', 'sources': [
            {'command_type': 'ope', 'num': 1, 'vertical': True}]},
        {'command_type': 'review', 'sources': []},
        {'command_type': 'review'},
        # 3+ columns already pack tightly
        {'command_type': '99', 'columns': 3},
        {'command_type': 'ope', 'operator': ['add'], 'a_max': 99, 'b_max': 99, 'columns': 3},
        # multi-line / widely-variable `ope` variants keep the gutter
        {'command_type': 'ope', 'operator': ['add'], 'vertical': True},
        {'command_type': 'ope', 'operator': ['mul'], 'intermediate': True},
        {'command_type': 'ope', 'operator': ['add'], 'use_parentheses': True},
        {'command_type': 'ope', 'operator': ['add'], 'missing_value': True},
        {'command_type': 'ope', 'mixed_operators': True},
        {'command_type': 'ope', 'terms_min': 3, 'terms_max': 5},
        {'command_type': 'ope', 'terms': 4},
        # a plain `ope` at 3+ columns already packs tightly
        {'command_type': 'ope', 'operator': ['mul'], 'a_digits': 3, 'b_digits': 2, 'columns': 3},
    ],
)
def test_everything_else_keeps_the_gutter_placement(data) -> None:
    assert three_layer_renderer._resolve_number_placement(data) == GUTTER


def test_columns_ceiling_overrides_a_short_command_type() -> None:
    assert three_layer_renderer._resolve_number_placement(
        {'command_type': 'squ', 'columns': 4}
    ) == GUTTER
