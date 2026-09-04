"""The group-4 (number-theory / comparison / approximation) `_generate_*_pdf`
builders delegate parameter resolution to the shared
`problem_generation.generate()` layer (issue #363, P2-4 under #357). This
completes P2: every `_generate_*_pdf` builder except `review` (handled in P3)
now routes through the shared layer.

Before #363 each builder re-derived its parameters inline -- `_generate_lcm_pdf`
/ `_generate_gcd_pdf` ran `resolve_digit_count_range` for the a/b ranges,
`_generate_evenodd_pdf` / `_generate_multiples_pdf` / `_generate_divisors_pdf`
read `a_min`/`a_max` and re-checked the `a_min >= 1` / `multiples_count` guards,
`_generate_compare_pdf` re-checked the fraction-digit range, and
`_generate_approx_pdf` called `resolve_approx_params` by hand -- then called
`nuts_calc_tex.generate_*` directly. After #363 the whole generation half is one
call: `problem_generation.generate(<command_type>, data, order, start_index)`.
These tests pin that delegation.

`_generate_compare_pdf` additionally stops hard-coding the CLI defaults
(different-denominators / proper / proper / fraction-vs-fraction): the shared
`_generate_compare_problems` -- unchanged, and already reachable via
`POST /generate-problems` -- now also serves `POST /generate-pdf`, so a
`comparison_pattern` / `a_fraction_form` / `b_fraction_form` / `a_kind` /
`b_kind` / `decimal_places` value sent to `/generate-pdf` is honoured instead of
silently dropped. No `frontend/web` preset sends those keys.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex  # noqa: E402
import three_layer_renderer  # noqa: E402

# One representative request per group-4 builder that resolves problems through
# the shared layer. The key is the builder render_worksheet_pdf's dispatch
# routes each request to; the value's `command_type` is what `generate()`
# receives.
_GROUP4_REQUESTS = {
    "_generate_evenodd_pdf": (
        "evenodd",
        {"paper_size": "A4", "command_type": "evenodd", "a_min": 1, "a_max": 100},
    ),
    "_generate_multiples_pdf": (
        "multiples",
        {"paper_size": "A4", "command_type": "multiples", "a_min": 2, "a_max": 12},
    ),
    "_generate_divisors_pdf": (
        "divisors",
        {"paper_size": "A4", "command_type": "divisors", "a_min": 6, "a_max": 60},
    ),
    "_generate_lcm_pdf": (
        "lcm",
        {"paper_size": "A4", "command_type": "lcm", "a_min": 4, "a_max": 40, "b_min": 4, "b_max": 40},
    ),
    "_generate_gcd_pdf": (
        "gcd",
        {"paper_size": "A4", "command_type": "gcd", "a_min": 4, "a_max": 40, "b_min": 4, "b_max": 40},
    ),
    "_generate_compare_pdf": (
        "compare",
        {"paper_size": "A4", "command_type": "compare"},
    ),
    "_generate_approx_pdf": (
        "approx",
        {"paper_size": "A4", "command_type": "approx", "kind": "round"},
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


@pytest.mark.parametrize("builder_name", sorted(_GROUP4_REQUESTS))
def test_group4_builder_delegates_to_shared_generate(
    builder_name, monkeypatch, tmp_path, _fake_engine
) -> None:
    expected_command_type, data = _GROUP4_REQUESTS[builder_name]

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


def test_group4_builder_surfaces_shared_layer_validation_error(
    tmp_path, _fake_engine
) -> None:
    """A validation ValueError raised inside the shared layer propagates out of
    the builder unchanged (app.py turns it into HTTP 500). Here: a `multiples`
    request with `a_min = 0` -- rejected by the `a_min >= 1` guard that issue
    #363 confirmed lives in `_generate_multiples_problems`.
    """
    data = {
        "paper_size": "A4", "command_type": "multiples", "a_min": 0, "a_max": 12,
    }
    with pytest.raises(ValueError, match="a_min must be at least 1 for the 'multiples' command."):
        three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))


def test_compare_builder_honours_shared_layer_comparison_pattern(
    monkeypatch, tmp_path, _fake_engine
) -> None:
    """After #363 `_generate_compare_pdf` no longer hard-codes the comparison
    pattern: a `comparison_pattern` sent to `POST /generate-pdf` reaches the
    shared `_generate_compare_problems`, which -- with default fraction kinds --
    forwards it to `nuts_calc_tex.generate_fraction_comparison_problems`.
    """
    captured = {}
    real = nuts_calc_tex.generate_fraction_comparison_problems

    def spy(pattern, *args, **kwargs):
        captured["pattern"] = pattern
        return real(pattern, *args, **kwargs)

    monkeypatch.setattr(
        three_layer_renderer.problem_generation.nuts_calc_tex,
        "generate_fraction_comparison_problems",
        spy,
    )

    data = {
        "paper_size": "A4", "command_type": "compare",
        "comparison_pattern": "same-denominator",
    }
    three_layer_renderer.render_worksheet_pdf(data, str(tmp_path))

    assert captured["pattern"] == "same-denominator"
