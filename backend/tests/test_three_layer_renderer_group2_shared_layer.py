"""The group-2 (`mixed` / single-shot generation) `_generate_*_pdf` builders
delegate parameter resolution to the shared `problem_generation.generate()`
layer (issue #361, P2-2 under #357).

Before #361 each builder re-derived its parameters inline -- `_generate_com_pdf`
called `validate_com_target` then `generate_com_problems`; the `99`/`squ`/`pi`
builders resolved `a_value`/`descend`/`shuffle` by hand; `_generate_mixed_pdf`
duplicated the fraction-digit / decimal-places / operand-kind / operator /
reducible_mode validation and `_generate_multi_term_mixed_pdf` pre-resolved the
term range -- then called `nuts_calc_tex.generate_*` directly. After #361 the
whole generation half is one call: `problem_generation.generate(<command_type>,
data, order, start_index)`. These tests pin that delegation.

`command_type == '100'` is group 2 too but is deliberately excluded: a single
10x10 table has no `count`-many problem list, so `_generate_hundred_square_pdf`
keeps its dedicated table path and never calls `generate()` (which raises a
targeted ValueError for `'100'`). `test_hundred_square_pdf_does_not_call_shared_generate`
pins that.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402

# One representative request per group-2 builder that resolves problems through
# the shared layer. The key is the builder render_worksheet_pdf's dispatch
# routes each request to; the value's `command_type` is what `generate()`
# receives.
_GROUP2_REQUESTS = {
    "_generate_com_pdf": (
        "com",
        {"paper_size": "A4", "command_type": "com", "a_value": 10},
    ),
    "_generate_kuku_pdf": (
        "99",
        {
            "paper_size": "A4", "command_type": "99", "a_value": 7,
            "descend": True, "shuffle": True, "reverse": True,
        },
    ),
    "_generate_abc_pdf": (
        "aBc",
        {"paper_size": "A4", "command_type": "aBc"},
    ),
    "_generate_squ_pdf": (
        "squ",
        {"paper_size": "A4", "command_type": "squ", "a_value": 3, "reverse": True},
    ),
    "_generate_pi_pdf": (
        "pi",
        {"paper_size": "A4", "command_type": "pi", "a_value": 2, "descend": True},
    ),
    "_generate_mixed_pdf__plain": (
        "mixed",
        {
            "paper_size": "A4", "command_type": "mixed",
            "a_kind": ["int"], "b_kind": ["int"], "operator": ["add"],
        },
    ),
    "_generate_mixed_pdf__multi_term": (
        "mixed",
        {
            "paper_size": "A4", "command_type": "mixed",
            "a_kind": ["int"], "b_kind": ["int"], "operator": ["add"], "terms": 3,
        },
    ),
}


@pytest.fixture
def _fake_engine(monkeypatch):
    """Let render_worksheet_pdf reach the builders without a real LaTeX run."""
    monkeypatch.setattr(
        three_layer_renderer.shutil, "which", lambda binary_name: "/usr/bin/" + binary_name
    )

    def fake_compile(self, tex_source, out_pdf_path):
        with open(out_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        nuts_calc_tex.LuaLatexEngineAdapter, "compile", fake_compile, raising=False
    )
    monkeypatch.setattr(
        nuts_calc_tex.PdflatexEngineAdapter, "compile", fake_compile, raising=False
    )


@pytest.mark.parametrize("builder_name", sorted(_GROUP2_REQUESTS))
def test_group2_builder_delegates_to_shared_generate(
    builder_name, monkeypatch, tmp_path, _fake_engine
) -> None:
    expected_command_type, data = _GROUP2_REQUESTS[builder_name]

    calls = []
    real_generate = three_layer_renderer.problem_generation.generate

    def spy_generate(command_type, params, count, start_index):
        calls.append((command_type, params, count, start_index))
        return real_generate(command_type, params, count, start_index)

    monkeypatch.setattr(three_layer_renderer.problem_generation, "generate", spy_generate)

    filepath, _ = three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))

    assert Path(filepath).read_bytes().startswith(b"%PDF")
    # Exactly one page of problems for these single-page builders, produced by
    # the shared layer with the request dict passed straight through and the
    # presentation layer's per-page order / start_index.
    assert len(calls) == 1
    command_type, params, count, start_index = calls[0]
    assert command_type == expected_command_type
    assert params is data
    assert count == nuts_calc_tex.DEFAULT_ROWS * 2  # rows * columns (columns default 2)
    assert start_index == 1


def test_group2_builder_surfaces_shared_layer_validation_error(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """A validation ValueError raised inside the shared layer propagates out of
    the builder unchanged (app.py turns it into HTTP 500). Here: a `mixed`
    request with an unknown operator -- rejected by the shared layer's
    `_validate_mixed_operators`, which issue #361 moved out of
    `_generate_mixed_pdf` so `POST /generate-problems` rejects it too.
    """
    data = {
        "paper_size": "A4", "command_type": "mixed",
        "a_kind": ["int"], "b_kind": ["int"], "operator": ["bogus"],
    }
    with pytest.raises(ValueError, match="operator must contain only"):
        three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))


def test_hundred_square_pdf_does_not_call_shared_generate(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """`100` stays on its dedicated table path: `_generate_hundred_square_pdf`
    resolves its axes via `problem_generation.resolve_hundred_square_axes` and
    never calls `generate()` (which raises a targeted ValueError for `'100'`).
    """
    calls = []
    real_generate = three_layer_renderer.problem_generation.generate
    monkeypatch.setattr(
        three_layer_renderer.problem_generation,
        "generate",
        lambda *args: calls.append(args) or real_generate(*args),
    )

    data = {
        "paper_size": "A4", "command_type": "100",
        "a_min": 1, "a_max": 10, "b_min": 1, "b_max": 10,
    }
    filepath, _ = three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))

    assert Path(filepath).read_bytes().startswith(b"%PDF")
    assert calls == []
