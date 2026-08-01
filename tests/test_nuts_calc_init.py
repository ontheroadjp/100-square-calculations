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
# --vertical validation
# ---------------------------------------------------------------------------


def test_init_vertical_requires_ope_command(monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "99", "-a", "3", "--vertical")
    assert exc_info.value.code == 1


def test_init_vertical_rejects_intermediate_combination(monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "ope", "--vertical", "--intermediate")
    assert exc_info.value.code == 1


@pytest.mark.parametrize("operator", ["div", "mix"])
def test_init_vertical_rejects_unsupported_operators(monkeypatch, operator):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "ope", "--vertical", "-o", operator)
    assert exc_info.value.code == 1


def test_init_vertical_rejects_multi_digit_mul_second_operand(monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        _init_with(monkeypatch, "A4", "ope", "--vertical", "-o", "mul", "-b", "2")
    assert exc_info.value.code == 1


@pytest.mark.parametrize("operator", ["add", "sub", "mul"])
def test_init_vertical_allows_supported_operators(monkeypatch, operator):
    args = _init_with(monkeypatch, "A4", "ope", "--vertical", "-o", operator)
    assert args.vertical is True
