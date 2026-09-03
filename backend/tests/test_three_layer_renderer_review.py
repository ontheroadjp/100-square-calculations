"""Tests for the multi-source 'review' (総合) worksheet builder (issue #140).

`three_layer_renderer._generate_review_pdf` composes problems from several
distinct drills onto one page: it generates each `sources` entry through its
own data-layer function, concatenates the results, optionally shuffles them
(deterministically when `review_seed` is set), renumbers them 1..N per page,
and renders them through `nuts_calc_tex.build_review_slot_content_tex`, a
`kind`-dispatching Layer-3 content format.

Most tests here are pure-Python: they stub the LaTeX engine's `compile()` so
no real pdflatex/lualatex is needed, and assert on the generated TeX string
or on validation errors. One end-to-end test compiles a real PDF and is
skipped when neither engine is on PATH, mirroring
test_nuts_calc_tex_presentation_api.py's skip pattern.
"""

import shutil
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402


GRADE3_SOURCES = [
    {
        "command_type": "ope", "num": 4, "operator": ["add", "sub"],
        "a_min": 100, "a_max": 9999, "b_min": 100, "b_max": 9999, "carry_mode": "mixed",
    },
    {
        "command_type": "ope", "num": 4, "operator": ["mul"],
        "a_min": 10, "a_max": 999, "b_min": 2, "b_max": 9,
    },
    {
        "command_type": "ope", "num": 4, "operator": ["div"],
        "a_min": 10, "a_max": 81, "b_min": 2, "b_max": 9, "remainder_mode": "mixed",
    },
    {
        "command_type": "ope", "num": 4, "operator": ["add", "sub"],
        "a_min": 1, "a_max": 99, "b_min": 1, "b_max": 99,
        "a_decimal_places": 1, "b_decimal_places": 1,
    },
    {
        "command_type": "frac", "num": 4, "operator": ["add", "sub"],
        "numerator_digits": 1, "denominator_digits": 1,
        "same_denominator": True, "proper_operands": True, "proper_result": True,
    },
]


@pytest.fixture
def stub_engine(monkeypatch):
    """Make both LaTeX adapters resolvable and their compile() write a
    dummy PDF, capturing the generated TeX source for assertions."""
    monkeypatch.setattr(
        three_layer_renderer.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name
    )
    captured_tex = []

    def fake_compile(self, tex_source, out_pdf_path):
        captured_tex.append(tex_source)
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )
    return captured_tex


def _render(data, tmp_path):
    return three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))


# --- build_review_slot_content_tex dispatch (nuts_calc_tex.py) ---------------


def test_review_slot_content_dispatches_ope_to_the_ope_formatter() -> None:
    payload = nuts_calc_tex.OpeProblem(index=7, a=3, b=4, operator="add", c=7)
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="ope", payload=payload)
    assert (
        nuts_calc_tex.build_review_slot_content_tex(problem, False)
        == nuts_calc_tex.build_ope_slot_content_tex(payload, False)
    )


def test_review_slot_content_dispatches_frac_to_the_fraction_formatter() -> None:
    payload = nuts_calc_tex.FractionProblem(
        index=7,
        a=nuts_calc_tex.FractionOperand(1, 5),
        b=nuts_calc_tex.FractionOperand(2, 5),
        operator="add",
        c=Fraction(3, 5),
    )
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="frac", payload=payload)
    assert (
        nuts_calc_tex.build_review_slot_content_tex(problem, False)
        == nuts_calc_tex.build_fraction_slot_content_tex(payload, False)
    )


def test_review_slot_content_rejects_an_unknown_kind() -> None:
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="compare", payload=object())
    with pytest.raises(ValueError, match="no slot formatter for kind 'compare'"):
        nuts_calc_tex.build_review_slot_content_tex(problem, False)


# --- per-source generation (three_layer_renderer helpers) -------------------


def test_review_ope_source_yields_that_count_of_ope_kind_problems() -> None:
    problems = three_layer_renderer._review_ope_problems(GRADE3_SOURCES[1], 4)
    assert len(problems) == 4
    assert all(p.kind == "ope" for p in problems)
    assert all(isinstance(p.payload, nuts_calc_tex.OpeProblem) for p in problems)
    assert all(p.payload.operator == "mul" for p in problems)


def test_review_frac_source_yields_that_count_of_frac_kind_problems() -> None:
    problems = three_layer_renderer._review_frac_problems(GRADE3_SOURCES[4], 4)
    assert len(problems) == 4
    assert all(p.kind == "frac" for p in problems)
    assert all(isinstance(p.payload, nuts_calc_tex.FractionProblem) for p in problems)
    # same_denominator + proper_result: every operand pair shares a denominator
    # and the answer stays a proper fraction.
    for p in problems:
        assert p.payload.a.denominator == p.payload.b.denominator
        assert 0 < p.payload.c < 1


# --- _generate_review_pdf composition --------------------------------------


def test_review_pdf_interleaves_every_source_on_one_page(stub_engine, tmp_path) -> None:
    data = {"paper_size": "A4", "command_type": "review", "sources": GRADE3_SOURCES}
    response = _render(data, tmp_path)
    assert Path(response[0]).read_bytes().startswith(b"%PDF")
    assert len(stub_engine) == 1
    tex = stub_engine[0]
    # 20 numbered slots (5 sources x 4), a single page.
    assert tex.count("\\newpage") == 0
    for slot in range(1, 21):
        assert f"\\problemnumberstyle{{{slot})}}" in tex
    # both content formats are present: a division sign from the ope sources
    # and a \fractioneq{...} usage (not just its \newcommand) from the frac
    # source.
    assert "\\div" in tex
    assert "\\fractioneq{" in tex


def test_review_pdf_seed_makes_the_shuffle_deterministic(stub_engine, monkeypatch, tmp_path) -> None:
    @dataclass
    class _Tag:
        name: str

    def fake_ope(source, count):
        return [
            nuts_calc_tex.ReviewProblem(index=0, kind="ope", payload=_Tag(f"o{i}"))
            for i in range(count)
        ]

    def fake_frac(source, count):
        return [
            nuts_calc_tex.ReviewProblem(index=0, kind="frac", payload=_Tag(f"f{i}"))
            for i in range(count)
        ]

    monkeypatch.setattr(
        three_layer_renderer, "_REVIEW_SOURCE_GENERATORS",
        {"ope": fake_ope, "frac": fake_frac},
    )

    slot_orders = []

    def fake_build_document(paper_size, *, pages, **kwargs):
        slot_orders.append([p.payload.name for page in pages for p in page.problems])
        return "%PDF-stub-tex"

    monkeypatch.setattr(nuts_calc_tex, "build_presentation_document_tex", fake_build_document)

    base = {"paper_size": "A4", "command_type": "review", "sources": GRADE3_SOURCES}

    # 4 ope sources of 4 + 1 frac source of 4, each fake generator numbering
    # its own batch from 0, so the pre-shuffle order repeats o0..o3.
    identity = ["o0", "o1", "o2", "o3"] * 4 + ["f0", "f1", "f2", "f3"]

    _render({**base, "shuffle": True, "review_seed": 123}, tmp_path)
    _render({**base, "shuffle": True, "review_seed": 123}, tmp_path)
    assert slot_orders[0] == slot_orders[1]
    assert sorted(slot_orders[0]) == sorted(identity)
    assert slot_orders[0] != identity  # a seed=123 shuffle actually reorders

    _render({**base, "shuffle": False}, tmp_path)
    assert slot_orders[2] == identity


def test_review_pdf_honors_the_name_field(stub_engine, tmp_path) -> None:
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "with_name_field": True,
    }
    _render(data, tmp_path)
    assert "Name:" in stub_engine[0]


def test_review_pdf_generates_one_page_per_requested_page(stub_engine, tmp_path) -> None:
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "page": 3,
    }
    _render(data, tmp_path)
    tex = stub_engine[0]
    assert tex.count("\\newpage") == 2
    # slots keep counting up across pages (1..60).
    assert "\\problemnumberstyle{60)}" in tex


# --- validation -----------------------------------------------------------


@pytest.mark.parametrize(
    "sources, message",
    [
        (None, "non-empty 'sources' list"),
        ([], "non-empty 'sources' list"),
        (["not-an-object"], "must be an object"),
        ([{"command_type": "compare", "num": 20}], "is not supported"),
        ([{"command_type": "ope", "num": 0}], "integer num >= 1"),
        ([{"command_type": "ope", "num": 2.5}], "integer num >= 1"),
    ],
)
def test_review_pdf_rejects_a_bad_sources_list(stub_engine, tmp_path, sources, message) -> None:
    data = {"paper_size": "A4", "command_type": "review"}
    if sources is not None:
        data["sources"] = sources
    with pytest.raises(ValueError, match=message):
        _render(data, tmp_path)


@pytest.mark.parametrize(
    "weights, order, expected",
    [
        ([4, 4, 4, 4, 4], 20, [4, 4, 4, 4, 4]),  # weights already sum to order
        ([4, 4, 4, 4, 4], 10, [2, 2, 2, 2, 2]),  # the 10問 choice
        ([4, 4, 4, 4, 4], 30, [6, 6, 6, 6, 6]),  # the 30問 choice
        ([3, 1], 20, [15, 5]),
        ([1, 1, 1], 20, [7, 7, 6]),  # largest-remainder hands out the leftover
    ],
)
def test_distribute_review_counts_fills_the_grid_by_weight(weights, order, expected) -> None:
    counts = three_layer_renderer._distribute_review_counts(weights, order)
    assert counts == expected
    assert sum(counts) == order


def test_review_pdf_scales_source_weights_to_a_smaller_grid(stub_engine, monkeypatch, tmp_path) -> None:
    seen_counts = []

    def spy_ope(source, count):
        seen_counts.append(count)
        return three_layer_renderer._review_ope_problems(source, count)

    monkeypatch.setattr(
        three_layer_renderer, "_REVIEW_SOURCE_GENERATORS",
        {"ope": spy_ope, "frac": three_layer_renderer._review_frac_problems},
    )
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "rows": 5, "columns": 2,  # the 10問 layout
    }
    _render(data, tmp_path)
    # 4 ope sources, each scaled from weight 4 to 2 for a 10-slot grid.
    assert seen_counts == [2, 2, 2, 2]
    tex = stub_engine[0]
    for slot in range(1, 11):
        assert f"\\problemnumberstyle{{{slot})}}" in tex
    assert "\\problemnumberstyle{11)}" not in tex


def test_review_pdf_rejects_out_of_range_rows_or_columns(stub_engine, tmp_path) -> None:
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": [{"command_type": "ope", "num": 1}], "rows": 0, "columns": 1,
    }
    with pytest.raises(ValueError, match="at least"):
        _render(data, tmp_path)


# --- end to end (real LaTeX) --------------------------------------------------


@pytest.mark.skipif(
    shutil.which("lualatex") is None and shutil.which("pdflatex") is None,
    reason="needs lualatex or pdflatex on PATH",
)
def test_review_pdf_compiles_a_real_grade3_worksheet(tmp_path) -> None:
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "shuffle": True, "review_seed": 1,
    }
    filepath, filename = three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))
    assert filename.endswith(".pdf")
    assert Path(filepath).read_bytes().startswith(b"%PDF")
