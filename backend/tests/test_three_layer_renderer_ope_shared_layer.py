"""The six group-1 `ope` `_generate_*_pdf` builders delegate parameter
resolution to the shared `problem_generation.generate()` layer (issue #360,
P2-1 under #357).

Before #360 each builder re-derived the a/b range, operator, decimal places
and (for the tree / multi-term variants) the term-count range inline, then
called `nuts_calc_tex.generate_*` directly. After #360 the whole generation
half is one call: `problem_generation.generate('ope', data, order,
start_index)`. These tests pin that delegation -- the shared entry point is
what produces the problems, with the request dict passed through untouched
and the per-page `order` / `start_index` the presentation layer computes.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402

# One representative request per group-1 builder; the key names the builder
# render_worksheet_pdf's dispatch ladder routes each request to.
_GROUP1_REQUESTS = {
    "_generate_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "operator": ["add"],
        "a_min": 10, "a_max": 99, "b_min": 1, "b_max": 9,
    },
    "_generate_vertical_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "vertical": True,
        "operator": ["add"], "a_min": 10, "a_max": 99,
    },
    "_generate_intermediate_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "intermediate": True,
        "operator": ["mul"], "a_min": 11, "a_max": 99, "b_min": 1, "b_max": 9,
    },
    "_generate_tree_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "use_parentheses": True,
        "operator": ["add"], "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
    },
    "_generate_multi_term_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "operator": ["add"],
        "terms": 3, "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
    },
    "_generate_missing_value_ope_pdf": {
        "paper_size": "A4", "command_type": "ope", "missing_value": True,
        "operator": ["add"], "a_min": 1, "a_max": 9, "b_min": 1, "b_max": 9,
    },
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


@pytest.mark.parametrize("builder_name", sorted(_GROUP1_REQUESTS))
def test_group1_builder_delegates_to_shared_generate(
    builder_name, monkeypatch, tmp_path, _fake_engine
) -> None:
    data = _GROUP1_REQUESTS[builder_name]

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
    assert command_type == "ope"
    assert params is data
    assert count == nuts_calc_tex.DEFAULT_ROWS * 2  # rows * columns (columns default 2)
    assert start_index == 1


def test_group1_builder_surfaces_shared_layer_validation_error(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """A validation ValueError raised inside the shared layer propagates out
    of the builder unchanged (app.py turns it into HTTP 500). Here: an
    `intermediate` request whose operator is not a single 'mul' -- rejected by
    the shared layer's _validate_intermediate, the same way POST
    /generate-problems rejects it.
    """
    data = {
        "paper_size": "A4", "command_type": "ope", "intermediate": True,
        "operator": ["add"], "a_min": 1, "a_max": 9,
    }
    with pytest.raises(ValueError, match="single 'mul' operator"):
        three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))
