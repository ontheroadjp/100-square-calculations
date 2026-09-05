"""Tests for the multi-source 'review' (総合) worksheet builder (issue #140).

`three_layer_renderer._generate_review_pdf` composes problems from several
distinct drills onto one page: since issue #364 (#357 P3) it generates each
`sources` entry through the shared `problem_generation.generate()` layer,
concatenates the results, optionally shuffles them (deterministically when
`review_seed` is set), renumbers them 1..N per page, and renders them through
`nuts_calc_tex.build_review_slot_content_tex`, a `kind`-dispatching Layer-3
content format whose registry (`_REVIEW_SLOT_CONTENT_FORMATTERS`) now covers
every command type the shared layer supports.

Before #364 `review` had its own `_review_ope_problems` / `_review_frac_problems`
generators wired through `_REVIEW_SOURCE_GENERATORS`, accepted only
`command_type in {'ope', 'frac'}`, and forwarded just the handful of options
the grade-3 recipe used. P3 removed all of that: any shared-layer command type
is now a valid source with full option parity, and grade 3's worksheet output
is unchanged (verified byte-for-byte against the pre-#364 renderer with the
module RNG seeded identically).

Most tests here are pure-Python: they stub the LaTeX engine's `compile()` so
no real pdflatex/lualatex is needed, and assert on the generated TeX string
or on validation errors. One end-to-end test compiles a real PDF and is
skipped when neither engine is on PATH, mirroring
test_nuts_calc_tex_presentation_api.py's skip pattern.
"""

import random
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


def test_review_slot_content_dispatches_compare_to_the_comparison_formatter() -> None:
    payload = nuts_calc_tex.FractionComparisonProblem(
        index=7,
        a=nuts_calc_tex.FractionComparisonOperand(1, 3),
        b=nuts_calc_tex.FractionComparisonOperand(2, 3),
    )
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="compare", payload=payload)
    assert (
        nuts_calc_tex.build_review_slot_content_tex(problem, False)
        == nuts_calc_tex.build_fraction_comparison_slot_content_tex(payload, False)
    )


def test_review_slot_content_prepends_an_instruction_line_for_an_ambiguous_kind() -> None:
    # dec2frac shares the generic arrow-conversion visual with several other
    # kinds (issue #381), so build_review_slot_content_tex stacks a short
    # instruction line above the formatter's own body in a left-aligned
    # tabular (so the Layer-2 number box lines up with the block's vertical
    # centre, not its top line, and the shorter content line stays flush
    # with the instruction line's left edge instead of being centered under
    # it -- issue #383).
    payload = nuts_calc_tex.Dec2FracProblem(
        index=7, decimal_places=1, scaled_numerator=5, reduced=Fraction(1, 2)
    )
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="dec2frac", payload=payload)
    content_tex = nuts_calc_tex.build_review_slot_content_tex(problem, False)
    formatter_tex = nuts_calc_tex.build_dec2frac_slot_content_tex(payload, False)
    assert content_tex == (
        "\\begin{tabular}{@{}l@{}}"
        f"\\reviewinstructionstyle{{小数を分数になおしましょう}}\\\\[{nuts_calc_tex.REVIEW_INSTRUCTION_ROW_GAP_TEX}]"
        f"{formatter_tex}"
        "\\end{tabular}"
    )


def test_review_slot_content_omits_the_instruction_line_for_a_self_evident_kind() -> None:
    # ope shows its own operator, so it is not in _REVIEW_SLOT_INSTRUCTION_TEXT
    # and build_review_slot_content_tex returns the formatter's body unchanged
    # (matching test_review_slot_content_dispatches_ope_to_the_ope_formatter).
    payload = nuts_calc_tex.OpeProblem(index=7, a=3, b=4, operator="add", c=7)
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="ope", payload=payload)
    assert "\\reviewinstructionstyle" not in nuts_calc_tex.build_review_slot_content_tex(problem, False)


def test_review_slot_content_rejects_a_kind_with_no_review_slot() -> None:
    # `ope --vertical` has no review slot (it needs a tabular grid); its kind
    # is deliberately absent from _REVIEW_SLOT_CONTENT_FORMATTERS.
    problem = nuts_calc_tex.ReviewProblem(index=1, kind="vertical_ope", payload=object())
    with pytest.raises(ValueError, match="no slot formatter for kind 'vertical_ope'"):
        nuts_calc_tex.build_review_slot_content_tex(problem, False)


# --- source kind resolution (three_layer_renderer) -------------------------


@pytest.mark.parametrize(
    "source, expected_kind",
    [
        ({"command_type": "ope"}, "ope"),
        ({"command_type": "ope", "use_parentheses": True}, "tree_ope"),
        ({"command_type": "ope", "missing_value": True}, "missing_value_ope"),
        ({"command_type": "ope", "terms": 3}, "multi_term_ope"),
        ({"command_type": "ope", "mixed_operators": True}, "multi_term_ope"),
        ({"command_type": "ope", "intermediate": True}, "intermediate_ope"),
        ({"command_type": "frac"}, "frac"),
        ({"command_type": "compare"}, "compare"),
        ({"command_type": "evenodd"}, "evenodd"),
    ],
)
def test_resolve_review_source_kind(source, expected_kind) -> None:
    assert three_layer_renderer._resolve_review_source_kind(source) == expected_kind


def test_resolve_review_source_kind_rejects_vertical_ope() -> None:
    with pytest.raises(ValueError, match="vertical"):
        three_layer_renderer._resolve_review_source_kind(
            {"command_type": "ope", "vertical": True}
        )


# --- per-source generation (shared problem_generation.generate layer) ------


def test_review_pdf_generates_each_source_through_the_shared_layer(
    stub_engine, monkeypatch, tmp_path
) -> None:
    calls = []
    real_generate = three_layer_renderer.problem_generation.generate

    def spy_generate(command_type, params, count, start_index):
        calls.append((command_type, id(params), count, start_index))
        return real_generate(command_type, params, count, start_index)

    monkeypatch.setattr(
        three_layer_renderer.problem_generation, "generate", spy_generate
    )

    data = {"paper_size": "A4", "command_type": "review", "sources": GRADE3_SOURCES}
    _render(data, tmp_path)

    # One call per source, each handed its own source dict, the weight-scaled
    # count (4 each for the default 20-slot grid), and start_index 1.
    assert [c[0] for c in calls] == ["ope", "ope", "ope", "ope", "frac"]
    assert [c[2] for c in calls] == [4, 4, 4, 4, 4]
    assert {c[3] for c in calls} == {1}
    assert [c[1] for c in calls] == [id(s) for s in GRADE3_SOURCES]


def test_review_source_honours_options_the_prototype_dispatch_dropped(
    stub_engine, tmp_path
) -> None:
    # `different_denominators` was silently dropped by the removed
    # `_review_frac_problems`; through the shared layer it now takes effect.
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": [
            {
                "command_type": "frac", "num": 1, "operator": ["add"],
                "numerator_digits": 1, "denominator_digits": 2,
                "different_denominators": True, "proper_operands": True,
            }
        ],
    }
    _render(data, tmp_path)
    tex = stub_engine[0]
    assert "\\fractioneq{" in tex


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


def test_review_accepts_a_shared_layer_source_the_prototype_rejected(stub_engine, tmp_path) -> None:
    """Before #364 only 'ope'/'frac' sources were allowed (others were HTTP
    500); now any command type the shared layer supports is a valid source.
    An 'evenodd' + 'compare' mix renders onto one page."""
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": [
            {"command_type": "evenodd", "num": 1, "a_min": 1, "a_max": 100},
            {"command_type": "compare", "num": 1},
        ],
    }
    response = _render(data, tmp_path)
    assert Path(response[0]).read_bytes().startswith(b"%PDF")
    tex = stub_engine[0]
    for slot in range(1, 21):
        assert f"\\problemnumberstyle{{{slot})}}" in tex


def test_review_pdf_grade3_output_is_stable_for_a_fixed_module_seed(stub_engine, tmp_path) -> None:
    """The #364 shared-layer migration leaves grade 3's review worksheet
    unchanged: with the module RNG seeded identically the generated TeX is
    reproducible. (Byte-for-byte equality with the pre-#364 renderer was
    verified out of band against a HEAD worktree.)"""
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "shuffle": True, "review_seed": 7,
    }
    random.seed(20260904)
    _render(data, tmp_path)
    random.seed(20260904)
    _render(data, tmp_path)
    assert stub_engine[0] == stub_engine[1]


def test_review_pdf_seed_makes_the_shuffle_deterministic(stub_engine, monkeypatch, tmp_path) -> None:
    @dataclass
    class _Tag:
        name: str

    def fake_generate(command_type, params, count, start_index):
        prefix = "o" if command_type == "ope" else "f"
        return [_Tag(f"{prefix}{i}") for i in range(count)]

    monkeypatch.setattr(
        three_layer_renderer.problem_generation, "generate", fake_generate
    )

    slot_orders = []

    def fake_build_document(paper_size, *, pages, **kwargs):
        slot_orders.append([p.payload.name for page in pages for p in page.problems])
        return "%PDF-stub-tex"

    monkeypatch.setattr(nuts_calc_tex, "build_presentation_document_tex", fake_build_document)

    base = {"paper_size": "A4", "command_type": "review", "sources": GRADE3_SOURCES}

    # 4 ope sources of 4 + 1 frac source of 4, each fake generate() batch
    # numbered from 0, so the pre-shuffle order repeats o0..o3.
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
        # '100' (table envelope) and 'review' (no nesting) are the command
        # types the shared layer does not expose as review sources.
        ([{"command_type": "100", "num": 20}], "is not supported"),
        ([{"command_type": "review", "num": 20}], "is not supported"),
        ([{"command_type": "nonsense", "num": 20}], "is not supported"),
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
    real_generate = three_layer_renderer.problem_generation.generate

    def spy_generate(command_type, params, count, start_index):
        seen_counts.append((command_type, count))
        return real_generate(command_type, params, count, start_index)

    monkeypatch.setattr(
        three_layer_renderer.problem_generation, "generate", spy_generate
    )
    data = {
        "paper_size": "A4", "command_type": "review",
        "sources": GRADE3_SOURCES, "rows": 5, "columns": 2,  # the 10問 layout
    }
    _render(data, tmp_path)
    # every source scaled from weight 4 to 2 for a 10-slot grid.
    assert seen_counts == [("ope", 2), ("ope", 2), ("ope", 2), ("ope", 2), ("frac", 2)]
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
