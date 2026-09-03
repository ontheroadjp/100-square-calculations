"""Tests for nuts_calc_tex.py's --divide-through ("わり進み") div mode (issue
#349).

The pure-Python helper / generation tests need no LaTeX engine. The CLI
end-to-end and CLI-rejection tests run nuts_calc_tex.py as a subprocess and
auto-skip when `pdflatex` is not on PATH, mirroring test_nuts_calc_tex.py.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

NUTS_CALC_TEX = BACKEND_DIR / "nuts_calc_tex.py"
CLI_TIMEOUT_SECONDS = 60
GENERATION_SAMPLE_SIZE = 200

# Grade-4 小数÷整数 preset range: dividend 1.0..9.9, divisor 2..9.
G4_NUMS_A = list(range(10, 100))
G4_NUMS_B = list(range(2, 10))
# Grade-5 小数÷小数 preset range: dividend 1.0..9.9, divisor 1.0..9.9.
G5_NUMS_A = list(range(10, 100))
G5_NUMS_B = list(range(10, 100))


# --------------------------------------------------------------------------
# divide_through_quotient
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("a", "b", "a_dp", "b_dp", "expected"),
    [
        # grade 4 (whole divisor): the 10**base_places cancels, so the
        # quotient scaled to base_places+extra places is a*10**extra // b.
        (90, 4, 1, 0, (2, 225)),      # 9.0 / 4 = 2.25
        (94, 8, 1, 0, (3, 1175)),     # 9.4 / 8 = 1.175
        (75, 4, 1, 0, (3, 1875)),     # 7.5 / 4 = 1.875
        (7, 4, 0, 0, (2, 175)),       # 7 / 4 = 1.75 (integer dividend)
        # grade 5 (decimal divisor scaled up to a whole number first).
        (90, 25, 1, 1, (1, 36)),      # 9.0 / 2.5 = 3.6
        (96, 15, 1, 1, (1, 64)),      # 9.6 / 1.5 = 6.4
        (65, 4, 1, 1, (2, 1625)),     # 6.5 / 0.4 = 16.25
    ],
)
def test_divide_through_quotient_returns_scaled_terminating_quotient(
        a: int, b: int, a_dp: int, b_dp: int, expected: tuple[int, int],
    ) -> None:
    result = tex_module.divide_through_quotient(a, b, a_dp, b_dp)
    assert result is not None
    total_places, c = result
    assert (total_places, c) == expected
    # The rendered decimal equals the true quotient, checked in exact
    # integers: c / 10**total_places == a / (b * 10**(a_dp - b_dp)).
    assert c * b == a * 10 ** (total_places - (a_dp - b_dp))


@pytest.mark.parametrize(
    ("a", "b", "a_dp", "b_dp", "reason"),
    [
        (80, 4, 1, 0, "already exact at base_places (8.0 / 4 = 2.0)"),
        (36, 3, 1, 0, "already exact at base_places (3.6 / 3 = 1.2)"),
        (93, 3, 1, 0, "already exact -- whole quotient (9.3 / 3 = 3.1)"),
        (97, 7, 1, 0, "non-terminating (÷ 7)"),
        (91, 3, 1, 0, "non-terminating (÷ 3)"),
        (12, 8, 1, 0, "quotient below 1 (1.2 / 8 = 0.15)"),
        (5, 0, 1, 0, "zero divisor"),
        (90, 40, 1, 1, "disguised whole divisor (4.0)"),
    ],
)
def test_divide_through_quotient_rejects_non_divide_through_pairs(
        a: int, b: int, a_dp: int, b_dp: int, reason: str,
    ) -> None:
    assert tex_module.divide_through_quotient(a, b, a_dp, b_dp) is None, reason


def test_divide_through_quotient_respects_the_place_bound() -> None:
    # 9.3 / 8 = 1.1625 needs exactly MAX places (accepted); one tighter bound
    # rejects it.
    assert tex_module.divide_through_quotient(93, 8, 1, 0) == (4, 11625)
    assert tex_module.divide_through_quotient(
        93, 8, 1, 0, max_total_decimal_places=3,
    ) is None


# --------------------------------------------------------------------------
# find_divide_through_division_pair
# --------------------------------------------------------------------------

def test_find_divide_through_division_pair_finds_a_pair_in_each_preset_range() -> None:
    for nums_a, nums_b, a_dp, b_dp in (
        (G4_NUMS_A, G4_NUMS_B, 1, 0),
        (G5_NUMS_A, G5_NUMS_B, 1, 1),
    ):
        pair = tex_module.find_divide_through_division_pair(nums_a, nums_b, a_dp, b_dp)
        assert pair is not None
        assert tex_module.divide_through_quotient(*pair, a_dp, b_dp) is not None


def test_find_divide_through_division_pair_returns_none_when_impossible() -> None:
    # Every divisor is 3 -> either exact or non-terminating, never わり進み.
    assert tex_module.find_divide_through_division_pair(
        list(range(2, 10)), [3], 1, 0,
    ) is None


# --------------------------------------------------------------------------
# calc_div_divide_through
# --------------------------------------------------------------------------

def test_calc_div_divide_through_returns_operands_quotient_and_place_count() -> None:
    for _ in range(GENERATION_SAMPLE_SIZE):
        a, b, c, places = tex_module.calc_div_divide_through(
            90, 4, G4_NUMS_A, G4_NUMS_B, 1, 0,
        )
        assert (a, b, c, places) == tex_module.calc_div_divide_through(
            a, b, [a], [b], 1, 0,
        )
        assert a % b != 0                                   # genuine わり進み
        assert c * b == a * 10 ** (places - 1)              # 9.0/4=2.25: base_places 1
        assert places <= tex_module.MAX_DIVIDE_THROUGH_QUOTIENT_DECIMAL_PLACES


def test_calc_div_divide_through_uses_deterministic_fallback(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
    monkeypatch.setattr(tex_module, "MAX_OPERAND_RETRY_ATTEMPTS", 0)
    # 9.0 / 4 = 2.25 is the only わり進み pair in this range.
    a, b, c, places = tex_module.calc_div_divide_through(
        88, 4, [88, 90], [4], 1, 0,
    )
    assert (a, b, c, places) == (90, 4, 225, 2)


def test_calc_div_divide_through_raises_when_impossible() -> None:
    with pytest.raises(ValueError):
        tex_module.calc_div_divide_through(20, 3, [20, 30], [3], 1, 0)


# --------------------------------------------------------------------------
# generate_ope_problems
# --------------------------------------------------------------------------

def test_generate_ope_problems_divide_through_grade4() -> None:
    problems = tex_module.generate_ope_problems(
        G4_NUMS_A, G4_NUMS_B, ['div'],
        order=GENERATION_SAMPLE_SIZE, start_index=1,
        a_decimal_places=1, b_decimal_places=0, divide_through=True,
    )
    assert len(problems) == GENERATION_SAMPLE_SIZE
    for problem in problems:
        assert problem.operator == 'div'
        assert problem.a_decimal_places == 1
        assert problem.b_decimal_places == 0
        assert problem.remainder == 0
        assert problem.remainder_decimal_places == 0
        places = problem.result_decimal_places
        assert places is not None
        assert 2 <= places <= tex_module.MAX_DIVIDE_THROUGH_QUOTIENT_DECIMAL_PLACES
        # genuine divide-through: not exact at base_places (= 1 here).
        assert problem.a % problem.b != 0
        # the recorded quotient renders to the true value (exact integers).
        assert problem.c * problem.b == problem.a * 10 ** (places - 1)


def test_generate_ope_problems_divide_through_grade5_decimal_divisor() -> None:
    problems = tex_module.generate_ope_problems(
        G5_NUMS_A, G5_NUMS_B, ['div'],
        order=GENERATION_SAMPLE_SIZE, start_index=1,
        a_decimal_places=1, b_decimal_places=1, divide_through=True,
    )
    assert len(problems) == GENERATION_SAMPLE_SIZE
    for problem in problems:
        assert problem.operator == 'div'
        assert problem.b_decimal_places == 1
        assert problem.b % 10 != 0                          # divisor stays a decimal
        assert problem.remainder == 0
        places = problem.result_decimal_places
        assert places is not None
        assert 1 <= places <= tex_module.MAX_DIVIDE_THROUGH_QUOTIENT_DECIMAL_PLACES
        # base_places = a_dp - b_dp = 0 here, so c * b == a * 10**places.
        assert problem.c * problem.b == problem.a * 10 ** places


def test_generate_ope_problems_without_divide_through_is_unchanged() -> None:
    import random

    kwargs = dict(a_decimal_places=1, b_decimal_places=0)
    random.seed(5)
    baseline = tex_module.generate_ope_problems(
        G4_NUMS_A, G4_NUMS_B, ['div'], 40, 1, **kwargs,
    )
    random.seed(5)
    with_flag_off = tex_module.generate_ope_problems(
        G4_NUMS_A, G4_NUMS_B, ['div'], 40, 1, divide_through=False, **kwargs,
    )
    assert [
        (p.a, p.b, p.c, p.remainder, p.result_decimal_places) for p in baseline
    ] == [
        (p.a, p.b, p.c, p.remainder, p.result_decimal_places) for p in with_flag_off
    ]
    assert all(p.result_decimal_places is None for p in baseline)


def test_build_ope_slot_content_tex_renders_divide_through_quotient() -> None:
    # 9.0 / 4 = 2.25: no \cdots tail (remainder 0), quotient at 2 places.
    problem = tex_module.OpeProblem(
        index=1, a=90, b=4, operator='div', c=225,
        a_decimal_places=1, b_decimal_places=0,
        remainder=0, remainder_decimal_places=0, result_decimal_places=2,
    )
    filled = tex_module.build_ope_slot_content_tex(problem, show_answer=True)
    assert "\\cdots" not in filled
    assert "9.0 \\opspace \\div \\opspace 4 \\opspace = \\opspace 2.25" in filled


# --------------------------------------------------------------------------
# CLI (pdflatex-gated)
# --------------------------------------------------------------------------

pdflatex_required = pytest.mark.skipif(
    shutil.which("pdflatex") is None,
    reason="nuts_calc_tex.py requires a LaTeX distribution (pdflatex) on PATH",
)


def _run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("NUTS_CALC_TEX_ENGINE", "pdflatex")
    return subprocess.run(
        [sys.executable, str(NUTS_CALC_TEX), *args],
        cwd=tmp_path, capture_output=True, text=True,
        timeout=CLI_TIMEOUT_SECONDS, env=env,
    )


@pdflatex_required
def test_cli_ope_div_divide_through_generates_terminating_quotients(tmp_path: Path) -> None:
    result = _run_cli(
        tmp_path,
        "A4", "ope", "-o", "div", "--divide-through", "--a-decimal-places", "1",
        "--a-min", "10", "--a-max", "99", "--b-min", "2", "--b-max", "9",
        "-r", "5", "-c", "4", "--csv", "--with-bottom-answer", "--out-file", "result.pdf",
    )

    assert result.returncode == 0, result.stderr
    pdf = tmp_path / "result.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")
    for row in (tmp_path / "result.csv").read_text().strip().splitlines():
        _, _, a, operator, b, c, remainder = row.split(",")
        assert operator == "div"
        assert remainder in ("0", "0.0")               # divided through, no remainder
        # quotient carried past the dividend's one place, and terminating.
        assert "." in c and len(c.split(".")[1]) >= 2
        assert round(float(a) / int(b) - float(c), 9) == 0.0


@pdflatex_required
@pytest.mark.parametrize(
    "invalid_args",
    [
        ("-o", "add", "--divide-through"),
        ("-o", "div", "mul", "--divide-through"),
        ("-o", "div", "--divide-through", "--a-decimal-places", "1", "--b-decimal-places", "2"),
        ("-o", "div", "--divide-through", "--decimal-remainder", "--a-decimal-places", "1"),
        ("-o", "div", "--divide-through", "--no-remainder"),
        ("-o", "div", "--divide-through", "--quotient-digits", "2"),
        ("-o", "div", "--divide-through", "--a-decimal-places", "1", "--b-decimal-places", "1", "--integer-dividend"),
        ("-o", "div", "--divide-through", "--vertical", "--a-decimal-places", "1"),
        ("-o", "div", "--divide-through", "--use-parentheses", "--mixed-operators"),
        ("-o", "div", "--divide-through", "--missing-value"),
        ("-o", "div", "--divide-through", "--intermediate"),
    ],
)
def test_cli_ope_divide_through_rejects_invalid_combinations(
        tmp_path: Path, invalid_args: tuple[str, ...],
    ) -> None:
    result = _run_cli(tmp_path, "A4", "ope", *invalid_args, "--out-file", "result.pdf")

    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()


@pdflatex_required
def test_cli_ope_divide_through_non_terminating_range_fails(tmp_path: Path) -> None:
    # Every divisor is 3 -> exact or non-terminating, never わり進み.
    result = _run_cli(
        tmp_path,
        "A4", "ope", "-o", "div", "--divide-through", "--a-decimal-places", "1",
        "--a-min", "10", "--a-max", "99", "--b-min", "3", "--b-max", "3",
        "--out-file", "result.pdf",
    )

    assert result.returncode == 1
    assert not (tmp_path / "result.pdf").exists()
