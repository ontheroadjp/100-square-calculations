"""Tests for nuts_calc.py's _init() argument parsing and validation.

Some existing validation branches use bare `exit()` (SystemExit(None), which
maps to process exit code 0) instead of `exit(1)`. This is a known quirk
documented in docs/L3_implementation/nuts_calc.py.md (it is what lets
web/backend/app.py's `subprocess.run(..., check=True)` treat a rejected
request as a success). These tests pin that current behavior rather than
"fixing" it, since this file is a pre-refactor safety net.
"""

import sys

import pytest

import nuts_calc as nc


def _init_with(monkeypatch: pytest.MonkeyPatch, *args: str):
    monkeypatch.setattr(sys, "argv", ["nuts_calc.py", *args])
    return nc._init()


# ---------------------------------------------------------------------------
# digit-count -> min/max derivation (ope command)
# ---------------------------------------------------------------------------


def test_init_derives_min_max_from_digit_value_for_ope(monkeypatch):
    args = _init_with(monkeypatch, "A4", "ope", "-a", "2", "-b", "3")
    assert (args.a_min, args.a_max) == (10, 99)
    assert (args.b_min, args.b_max) == (100, 999)


@pytest.mark.parametrize(
    "digits,expected",
    [(1, (1, 9)), (2, (10, 99)), (3, (100, 999)), (4, (1000, 9999)), (5, (10000, 99999))],
)
def test_init_digit_value_covers_one_through_five_digits(monkeypatch, digits, expected):
    args = _init_with(monkeypatch, "A4", "ope", "-a", str(digits))
    assert (args.a_min, args.a_max) == expected


# ---------------------------------------------------------------------------
# required -a for com/99/squ/pi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command,extra", [("com", []), ("99", []), ("squ", []), ("pi", [])])
def test_init_requires_a_value_and_exits_with_code_none(monkeypatch, command, extra):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", command, *extra)
    # exit() with no argument raises SystemExit(None), which the OS reports
    # as process exit code 0 -- the known "silent success" quirk.
    assert exc_info.value.code is None


@pytest.mark.parametrize("command", ["com", "99", "squ", "pi"])
def test_init_intermediate_does_not_bypass_a_value_requirement(monkeypatch, command):
    # issue #4 Phase 1 (fixed): `if args.command == 'ope' or args.intermediate:`
    # used to let --intermediate skip the required -a check entirely for
    # com/99/squ/pi. Now only 'ope' takes that branch, so -a is still required.
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", command, "--intermediate")
    assert exc_info.value.code is None


# ---------------------------------------------------------------------------
# 100 command defaults and digit-count ceiling
# ---------------------------------------------------------------------------


def test_init_100_defaults_a_and_b_to_one_digit_when_unset(monkeypatch):
    args = _init_with(monkeypatch, "A4", "100")
    assert args.a_value == 1
    assert args.b_value == 1
    assert (args.a_min, args.a_max) == (1, 9)
    assert (args.b_min, args.b_max) == (1, 9)


def test_init_100_rejects_digit_value_above_three_with_exit_code_none(monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "100", "-a", "4")
    assert exc_info.value.code is None


# ---------------------------------------------------------------------------
# --intermediate validation (issue #4 Phase 3)
# ---------------------------------------------------------------------------


def test_init_intermediate_rejects_multi_digit_second_operand(monkeypatch):
    # nuts_calc.py's "aabb" intermediate value implements the 2-digit x
    # 1-digit mental-arithmetic technique from memo.md, which only holds when
    # b is single-digit (see tests/test_nuts_calc_data.py). A 2-digit b
    # silently drops its tens digit from the calculation, so it's rejected.
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "ope", "--intermediate", "-b", "2")
    assert exc_info.value.code == 1


def test_init_intermediate_allows_single_digit_second_operand(monkeypatch):
    args = _init_with(monkeypatch, "A4", "ope", "--intermediate")
    assert args.intermediate is True


# ---------------------------------------------------------------------------
# rows/columns lower bound (issue #4 Phase 9 follow-up)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["-r", "-c"])
def test_init_rejects_zero_rows_or_columns(monkeypatch, flag):
    # -r 0 / -c 0 used to reach main() and crash with ZeroDivisionError in
    # different spots (row_heights and frame-width calculations) rather than
    # failing with a clear message at argument-validation time.
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "ope", flag, "0")
    assert exc_info.value.code == 1
