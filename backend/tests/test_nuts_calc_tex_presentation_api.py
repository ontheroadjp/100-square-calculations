"""Unit and end-to-end tests for nuts_calc_tex.py's internal presentation
API (issue #183, B-4).

The presentation API composes Layer 1 (PageShell, #182), Layer 2
(ContentAreaLayout, #184), and a caller-supplied Layer 3 content_format
(#122's taxonomy) into a full LaTeX document, entirely via new, additive
code (build_presentation_document_tex/PresentationPage). It does not modify
build_document_tex/build_page_tex/build_preamble_tex or any
build_*_block_tex()/build_*_page_pair()/build_*_pages() function, which the
current production /generate-pdf (subprocess-based) still depends on
unmodified.

Most tests here are pure-Python (no pdflatex/lualatex required), exercising
build_presentation_document_tex's generated TeX string directly, using the
`com` command group's existing generate_com_problems (data logic) and
build_com_slot_content_tex (#184's number-free Layer-3 variant) as content
data/content_format. One end-to-end test compiles a real PDF via
PdflatexEngineAdapter to satisfy #183's Done Criteria ("produce a PDF ...
for at least one full command group"); it is skipped when pdflatex is not
on PATH, mirroring test_nuts_calc_tex.py's skip pattern.
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def _build_com_page(target: int, order: int, start_index: int) -> tuple[tex_module.PresentationPage, list[tex_module.ComProblem]]:
    problems = tex_module.generate_com_problems(target, order, start_index)
    indices = [problem.index for problem in problems]
    return tex_module.PresentationPage(problems=problems, indices=indices), problems


def test_build_presentation_document_tex_uses_custom_page_shell_header() -> None:
    page_shell = tex_module.PageShell(title_str="Custom Title", sub_title_str="Custom Subtitle")
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)
    page, _ = _build_com_page(target=10, order=1, start_index=1)

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=page_shell,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert "Custom Title" in tex
    assert "Custom Subtitle" in tex
    assert tex_module.DEFAULT_PAGE_SHELL.title_str not in tex


def test_build_presentation_document_tex_places_number_box_via_content_area_layout() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=12)
    page, problems = _build_com_page(target=10, order=1, start_index=5)

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
    )

    expected_slot = tex_module.build_content_area_slot_tex(
        problems[0].index, tex_module.build_com_slot_content_tex(problems[0], show_answer=True), layout
    )
    assert "\\makebox[12mm][l]{5)}" in tex
    assert expected_slot in tex


def test_build_presentation_document_tex_matches_content_area_slot_composition_for_com() -> None:
    """Every problem's rendered slot must equal directly composing Layer 2
    (build_content_area_slot_tex) over Layer 3 (build_com_slot_content_tex,
    #184's number-free variant), confirming build_presentation_document_tex
    is a faithful composition and not a divergent reimplementation."""
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=8)
    page, problems = _build_com_page(target=10, order=3, start_index=1)

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
    )

    for problem in problems:
        expected_slot = tex_module.build_content_area_slot_tex(
            problem.index, tex_module.build_com_slot_content_tex(problem, show_answer=True), layout
        )
        assert expected_slot in tex


def test_build_presentation_document_tex_show_answer_toggles_blank_vs_filled() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)
    page, problems = _build_com_page(target=10, order=1, start_index=1)

    blank_tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )
    filled_tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
    )

    assert tex_module.BOXED_BLANK_TEX in blank_tex
    assert str(problems[0].c) in filled_tex
    assert tex_module.BOXED_BLANK_TEX not in filled_tex


def test_build_presentation_document_tex_separates_multiple_pages_with_newpage() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)
    page_one, _ = _build_com_page(target=10, order=1, start_index=1)
    page_two, _ = _build_com_page(target=10, order=1, start_index=2)

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page_one, page_two],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
    )

    assert tex.count("\\newpage") == 1


def test_build_presentation_document_tex_appends_bottom_answer_tex() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)
    page, _ = _build_com_page(target=10, order=1, start_index=1)
    page = tex_module.PresentationPage(
        problems=page.problems, indices=page.indices, bottom_answer_tex="(1) 4"
    )

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
    )

    assert "(1) 4" in tex


def test_build_presentation_document_tex_grid_layout_dispatches_to_tabular_and_block() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)
    page, _ = _build_com_page(target=10, order=1, start_index=1)

    tabular_tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
        grid_layout='tabular',
    )
    block_tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=True,
        grid_layout='block',
    )

    assert "\\begin{tabular}" in tabular_tex
    assert "\\vfill\n" in block_tex


@pytest.mark.skipif(
    shutil.which("pdflatex") is None,
    reason="requires pdflatex on PATH to compile the presentation API's output into a real PDF",
)
def test_build_presentation_document_tex_produces_a_pdf_for_com_command_group(tmp_path: Path) -> None:
    layout = tex_module.CONTENT_AREA_LAYOUT_PRESETS[10]
    page, _ = _build_com_page(target=10, order=10, start_index=1)
    engine_adapter = tex_module.PdflatexEngineAdapter()

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_com_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=engine_adapter,
        show_answer=False,
    )
    out_pdf_path = tmp_path / "presentation_com.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))

    assert out_pdf_path.exists()
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
