"""Tests for the shared "grid table" content-format component
(taxonomy pattern 7) introduced by issue #270.

Issue #270 retrofits ``build_hundred_square_block_tex`` (the ``100`` addition
table) so its whole-block ``tabular`` is emitted through the shared
``\\hundredsquarecell`` component and the centralized
``\\hundredsquarecellwidth`` / ``\\hundredsquarecolsep`` /
``\\hundredsquarerulewidth`` lengths + ``\\hundredsquareheadercolor`` name,
instead of inline ``tabular`` metrics and literal ``lightgray`` colours at the
call site.

- Every header and data entry is wrapped in ``\\hundredsquarecell`` (a
  fixed-width centered ``\\hbox to``) so a 1- or 2-digit number occupies the
  same width and no column goes ragged (guidelines items 6, 11, 20).
- ``\\tabcolsep`` and ``\\arrayrulewidth`` are set from the two lengths inside
  the ``center`` group (guidelines items 6, 12); both default to LaTeX's own
  values, so this is centralization only with no visual change.
- ``\\hbox to`` (not ``\\makebox[``) is used so #229's "``\\makebox[`` absent
  => the Layer-2 number box was skipped" assertions on the ``100`` path stay
  meaningful.

The ``100`` command reaches both document builders: the legacy CLI path
(``build_document_tex``, also used by ``POST /generate-pdf``) and the internal
presentation API (``build_presentation_document_tex`` with
``ContentAreaLayout(numbered=False)``, used by ``POST /generate-problems``).
Both splice ``build_content_format_macros_tex()``. Each real-PDF spot check is
skipped when its engine binary is absent (mirroring
test_nuts_calc_tex_staged_arrow_chain_content_format.py).
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def _table(size: int = tex_module.HUNDRED_SQUARE_SIZE) -> "tex_module.HundredSquareTable":
    return tex_module.HundredSquareTable(
        left_values=list(range(1, size + 1)),
        top_values=list(range(1, size + 1)),
    )


# --- shared macro block -----------------------------------------------------

def test_content_format_macros_define_the_hundred_square_grid_components() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newlength{\\hundredsquarecellwidth}" in macros
    assert (
        f"\\setlength{{\\hundredsquarecellwidth}}{{{tex_module.CONTENT_FORMAT_HUNDRED_SQUARE_CELL_WIDTH_TEX}}}"
        in macros
    )
    assert "\\newlength{\\hundredsquarecolsep}" in macros
    assert (
        f"\\setlength{{\\hundredsquarecolsep}}{{{tex_module.CONTENT_FORMAT_HUNDRED_SQUARE_COLSEP_TEX}}}"
        in macros
    )
    assert "\\newlength{\\hundredsquarerulewidth}" in macros
    assert (
        f"\\setlength{{\\hundredsquarerulewidth}}{{{tex_module.CONTENT_FORMAT_HUNDRED_SQUARE_RULE_WIDTH_TEX}}}"
        in macros
    )
    assert (
        f"\\newcommand{{\\hundredsquareheadercolor}}{{{tex_module.HUNDRED_SQUARE_HEADER_COLOR}}}"
        in macros
    )
    assert (
        "\\newcommand{\\hundredsquarecell}[1]{\\hbox to \\hundredsquarecellwidth{\\hfil #1\\hfil}}"
        in macros
    )
    # \makebox[ is deliberately NOT used here: #229's layout tests assert its
    # absence as a proxy for "the problem-number box was skipped".
    assert "\\makebox[" not in macros


def test_content_format_macros_leave_the_pattern_1_to_5_definitions_intact() -> None:
    macros = tex_module.build_content_format_macros_tex()

    assert "\\newcommand{\\opspace}{\\hspace{\\opspacewidth}}" in macros
    assert "\\newcommand{\\horizontaleq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractioneq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\boxedblank}{\\fbox{\\rule[-0.2em]{0pt}{0.9em}\\hspace{\\boxedblankwidth}}}" in macros
    assert "\\newcommand{\\boxedblankeq}[1]{$#1\\vphantom{\\boxedblank}$}" in macros
    assert "\\newcommand{\\compareeq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert "\\newcommand{\\arroweq}[1]{$#1$}" in macros
    assert "\\newcommand{\\fractionarroweq}[1]{\\problemfractionstyle{$\\displaystyle #1\\vphantom{\\frac{0}{0}}$}}" in macros
    assert (
        "\\newcommand{\\stagechainarrow}{\\hspace{\\stagechaingapwidth}\\Rightarrow\\hspace{\\stagechaingapwidth}}"
        in macros
    )
    assert (
        "\\newcommand{\\stagechainmemo}[1]{\\hbox to \\stagechainmemowidth{\\hfil\\ensuremath{#1}\\hfil}}"
        in macros
    )
    assert "\\newcommand{\\stagedchaineq}[1]{$#1\\vphantom{0}$}" in macros


def test_macros_are_spliced_into_the_legacy_document_builder() -> None:
    table = _table()
    blank_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=False)],
        columns=1,
        layout="block",
    )
    filled_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=True)],
        columns=1,
        layout="block",
    )
    document = tex_module.build_document_tex(
        "A4", [blank_page], [filled_page], "blank", tex_module.PdflatexEngineAdapter()
    )

    assert "\\newcommand{\\hundredsquarecell}" in document
    assert document.index("\\newcommand{\\hundredsquarecell}") < document.index("\\begin{document}")


def test_macros_are_spliced_into_the_presentation_document_builder() -> None:
    table = _table()
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, numbered=False)
    page = tex_module.PresentationPage(problems=[table], indices=[1])

    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_hundred_square_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=tex_module.PdflatexEngineAdapter(),
        show_answer=False,
        grid_layout="block",
    )

    assert "\\newcommand{\\hundredsquarecell}" in tex
    assert tex.index("\\newcommand{\\hundredsquarecell}") < tex.index("\\begin{document}")
    # #229 invariant on the unnumbered `100` path: no Layer-2 number box.
    assert "\\makebox[" not in tex


# --- grid body helper ---------------------------------------------------

def test_build_hundred_square_grid_tex_routes_every_entry_through_the_shared_cell() -> None:
    table = tex_module.HundredSquareTable(
        left_values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 1],
        top_values=[10, 20, 30, 40, 50, 60, 70, 80, 90, 15],
    )

    blank = tex_module.build_hundred_square_grid_tex(table, show_answer=False)
    filled = tex_module.build_hundred_square_grid_tex(table, show_answer=True)

    # centralized geometry, applied inside the center group
    assert "\\begin{center}\n\\setlength{\\tabcolsep}{\\hundredsquarecolsep}\n" in blank
    assert "\\setlength{\\arrayrulewidth}{\\hundredsquarerulewidth}\n" in blank
    # centralized header colour, no inline literal at the call site
    assert ">{\\columncolor{\\hundredsquareheadercolor}}c|" in blank
    assert "\\rowcolor{\\hundredsquareheadercolor} \\hundredsquarecell{}" in blank
    assert "\\columncolor{lightgray}" not in blank
    assert "\\rowcolor{lightgray}" not in blank
    # every header entry is wrapped
    assert "\\hundredsquarecell{10}" in blank and "\\hundredsquarecell{15}" in blank
    # blank data cells are empty fixed-width boxes; the sums are hidden
    assert "\\hundredsquarecell{}" in blank
    assert "11" not in blank  # 1 + 10
    # filled data cells carry the sums, still wrapped
    assert "\\hundredsquarecell{11}" in filled
    # #229 invariant: no \makebox[ leaks into the grid
    assert "\\makebox[" not in blank and "\\makebox[" not in filled


def test_build_hundred_square_grid_tex_emits_one_rule_per_row_plus_borders() -> None:
    table = _table()
    grid = tex_module.build_hundred_square_grid_tex(table, show_answer=True)

    # 1 top border + 1 under the header + 1 under each of the 10 data rows
    assert grid.count("\\hline") == tex_module.HUNDRED_SQUARE_SIZE + 2
    # every data row and the header row is terminated
    assert grid.count("\\\\") == tex_module.HUNDRED_SQUARE_SIZE + 1


# --- delegation chain (block == grid == slot) --------------------------

def test_block_and_slot_delegate_to_the_shared_grid_helper() -> None:
    table = _table()

    for show_answer in (False, True):
        grid = tex_module.build_hundred_square_grid_tex(table, show_answer=show_answer)
        block = tex_module.build_hundred_square_block_tex(table, show_answer=show_answer)
        slot = tex_module.build_hundred_square_slot_content_tex(table, show_answer=show_answer)

        assert block == grid
        assert slot == block
        # the grid still carries no per-problem number prefix (pattern 7)
        assert "makebox" not in slot


# --- real-PDF spot checks (both engines, blank + filled) --------------

_ENGINES = {
    "pdflatex": tex_module.PdflatexEngineAdapter,
    "lualatex": tex_module.LuaLatexEngineAdapter,
}


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
@pytest.mark.parametrize("mode", ["blank", "filled"])
def test_hundred_square_page_compiles_to_pdf(engine_name: str, mode: str, tmp_path: Path) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    table = tex_module.generate_hundred_square(list(range(1, 10)), list(range(1, 10)))
    blank_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=False)],
        columns=1,
        layout="block",
    )
    filled_page = tex_module.Page(
        blocks=[tex_module.build_hundred_square_block_tex(table, show_answer=True)],
        columns=1,
        layout="block",
    )
    tex = tex_module.build_document_tex(
        "A4", [blank_page], [filled_page], mode, engine_adapter
    )
    out_pdf_path = tmp_path / f"{engine_name}_{mode}.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500


@pytest.mark.parametrize("engine_name", sorted(_ENGINES))
def test_hundred_square_presentation_api_page_compiles_to_pdf(engine_name: str, tmp_path: Path) -> None:
    if shutil.which(engine_name) is None:
        pytest.skip(f"requires {engine_name} on PATH")
    engine_adapter = _ENGINES[engine_name]()
    table = tex_module.generate_hundred_square(list(range(1, 10)), list(range(1, 10)))
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, numbered=False)
    page = tex_module.PresentationPage(problems=[table], indices=[1])
    tex = tex_module.build_presentation_document_tex(
        "A4",
        pages=[page],
        content_format=tex_module.build_hundred_square_slot_content_tex,
        page_shell=tex_module.DEFAULT_PAGE_SHELL,
        content_area_layout=layout,
        engine_adapter=engine_adapter,
        show_answer=False,
        grid_layout="block",
    )
    out_pdf_path = tmp_path / f"{engine_name}_presentation.pdf"
    engine_adapter.compile(tex, str(out_pdf_path))
    data = out_pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 500
