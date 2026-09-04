"""The group-3 (fraction-family) `_generate_*_pdf` builders delegate parameter
resolution to the shared `problem_generation.generate()` layer (issue #362, P2-3
under #357).

Before #362 each builder re-derived its parameters inline -- `_generate_frac_pdf`
ran ~50 lines of numerator/denominator digit, operator, fraction-form and
`reducible_mode` validation; `_generate_simplify_pdf` / `_generate_frac2dec_pdf` /
`_generate_commondenom_pdf` re-checked the fraction-digit range; `_generate_divfrac_pdf`
resolved the a/b ranges and the `b_min >= 1` guard by hand -- then called
`nuts_calc_tex.generate_*` directly. After #362 the whole generation half is one
call: `problem_generation.generate(<command_type>, data, order, start_index)`.
These tests pin that delegation.

The `frac` builder's operator / fraction-form / `reducible_mode`-value allowlists
were builder-only before #362; the P2-3 migration moves them into
`_generate_frac_problems` so `POST /generate-problems` rejects the same malformed
values, per the #357 /mtg "shared layer takes the stricter side" decision.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402

# One representative request per group-3 builder that resolves problems through
# the shared layer. The key is the builder render_worksheet_pdf's dispatch
# routes each request to; the value's `command_type` is what `generate()`
# receives.
_GROUP3_REQUESTS = {
    "_generate_frac_pdf": (
        "frac",
        {"paper_size": "A4", "command_type": "frac", "operator": ["add"]},
    ),
    "_generate_simplify_pdf": (
        "simplify",
        {"paper_size": "A4", "command_type": "simplify"},
    ),
    "_generate_commondenom_pdf": (
        "commondenom",
        {"paper_size": "A4", "command_type": "commondenom"},
    ),
    "_generate_divfrac_pdf": (
        "divfrac",
        {"paper_size": "A4", "command_type": "divfrac"},
    ),
    "_generate_frac2dec_pdf": (
        "frac2dec",
        {"paper_size": "A4", "command_type": "frac2dec"},
    ),
    "_generate_dec2frac_pdf": (
        "dec2frac",
        {"paper_size": "A4", "command_type": "dec2frac"},
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


@pytest.mark.parametrize("builder_name", sorted(_GROUP3_REQUESTS))
def test_group3_builder_delegates_to_shared_generate(
    builder_name, monkeypatch, tmp_path, _fake_engine
) -> None:
    expected_command_type, data = _GROUP3_REQUESTS[builder_name]

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


def test_group3_builder_surfaces_shared_layer_validation_error(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """A validation ValueError raised inside the shared layer propagates out of
    the builder unchanged (app.py turns it into HTTP 500). Here: a `frac`
    request with an unsupported operator -- rejected by the operator allowlist
    that issue #362 moved out of `_generate_frac_pdf` so `POST /generate-problems`
    rejects it too.
    """
    data = {
        "paper_size": "A4", "command_type": "frac", "operator": ["bogus"],
    }
    with pytest.raises(ValueError, match="operator contains an unsupported value for the 'frac' command."):
        three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))


def test_frac_builder_surfaces_shared_layer_reducible_mode_error(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """The `reducible_mode` value allowlist is likewise shared after #362: an
    unknown `reducible_mode` is rejected with the old builder's wording.
    """
    data = {
        "paper_size": "A4", "command_type": "frac",
        "operator": ["mul"], "reducible_mode": "bogus",
    }
    with pytest.raises(ValueError, match="Unknown reducible_mode for the 'frac' command."):
        three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))
