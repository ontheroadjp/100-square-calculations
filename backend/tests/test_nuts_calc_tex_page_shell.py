"""Unit tests for nuts_calc_tex.py's PageShell abstraction (issue #182).

PageShell is Layer 1 of #166's presentation-layer model (header / margins /
content-area boundary / footer). #182 extracts it as an explicit, named,
additive unit without changing production output: build_preamble_tex,
build_page_header_tex, and build_page_tex become thin wrappers around
build_page_shell_preamble_tex/build_page_shell_header_tex/
build_page_shell_body_tex with DEFAULT_PAGE_SHELL. These tests exercise the
pure-Python PageShell builders directly (no pdflatex/lualatex required),
complementing the pdflatex-gated end-to-end assertions on the wrapper
functions in test_nuts_calc_tex.py.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_default_page_shell_matches_current_layout_constants() -> None:
    shell = tex_module.DEFAULT_PAGE_SHELL

    assert shell.header_str == tex_module.HEADER_STR
    assert shell.title_str == tex_module.TITLE_STR
    assert shell.sub_title_str == tex_module.SUB_TITLE_STR
    assert shell.copyright_str == tex_module.COPYRIGHT_STR
    assert shell.side_margin_mm == tex_module.PAGE_SIDE_MARGIN_MM
    assert shell.top_margin_mm == tex_module.PAGE_TOP_MARGIN_MM
    assert shell.bottom_margin_mm == tex_module.PAGE_BOTTOM_MARGIN_MM
    assert shell.footer_text_lowering_mm == tex_module.FOOTER_TEXT_LOWERING_MM


def test_build_preamble_tex_matches_page_shell_builder_for_every_paper_size() -> None:
    for paper_size in tex_module.PAPER_SIZE_TO_GEOMETRY_OPTION:
        wrapper_tex = tex_module.build_preamble_tex(paper_size)
        page_shell_tex = tex_module.build_page_shell_preamble_tex(
            tex_module.DEFAULT_PAGE_SHELL, paper_size
        )
        assert wrapper_tex == page_shell_tex


def test_build_preamble_tex_matches_page_shell_builder_for_lualatex_adapter() -> None:
    adapter = tex_module.LuaLatexEngineAdapter()

    wrapper_tex = tex_module.build_preamble_tex("A4", adapter)
    page_shell_tex = tex_module.build_page_shell_preamble_tex(
        tex_module.DEFAULT_PAGE_SHELL, "A4", adapter
    )

    assert wrapper_tex == page_shell_tex


def test_build_page_header_tex_matches_page_shell_builder_without_name_field() -> None:
    wrapper_tex = tex_module.build_page_header_tex()
    page_shell_tex = tex_module.build_page_shell_header_tex(tex_module.DEFAULT_PAGE_SHELL)

    assert wrapper_tex == page_shell_tex


def test_build_page_header_tex_matches_page_shell_builder_with_name_field() -> None:
    wrapper_tex = tex_module.build_page_header_tex(with_name_field=True)
    page_shell_tex = tex_module.build_page_shell_header_tex(
        tex_module.DEFAULT_PAGE_SHELL, with_name_field=True
    )

    assert wrapper_tex == page_shell_tex


def test_build_page_tex_matches_page_shell_body_builder_for_inline_layout() -> None:
    page = tex_module.Page(blocks=["1) $1 + 1 = 2$"], columns=1, layout="inline")

    wrapper_tex = tex_module.build_page_tex(page)
    grid_tex = tex_module.build_inline_grid_tex(page.blocks, page.columns)
    page_shell_tex = tex_module.build_page_shell_body_tex(tex_module.DEFAULT_PAGE_SHELL, grid_tex)

    assert wrapper_tex == page_shell_tex


def test_build_page_tex_matches_page_shell_body_builder_with_bottom_answer() -> None:
    page = tex_module.Page(
        blocks=["1) $1 + 1 = 2$"], columns=1, layout="inline", bottom_answer_tex="1) 2"
    )

    wrapper_tex = tex_module.build_page_tex(page, with_name_field=True)
    grid_tex = tex_module.build_inline_grid_tex(page.blocks, page.columns)
    page_shell_tex = tex_module.build_page_shell_body_tex(
        tex_module.DEFAULT_PAGE_SHELL, grid_tex, with_name_field=True, bottom_answer_tex="1) 2"
    )

    assert wrapper_tex == page_shell_tex


def test_page_shell_with_overridden_margins_changes_geometry_line() -> None:
    custom_shell = tex_module.PageShell(side_margin_mm=25, top_margin_mm=30, bottom_margin_mm=50)

    tex = tex_module.build_page_shell_preamble_tex(custom_shell, "A4")

    assert "margin=25mm,top=30mm,bottom=50mm" in tex
    assert "margin=15mm,top=20mm,bottom=40mm" not in tex
