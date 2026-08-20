"""Unit tests for nuts_calc_tex.py's ContentAreaLayout abstraction (issue #184).

ContentAreaLayout is Layer 2 of #166's presentation-layer model (content-area
grid template: problem-slot count/arrangement and number-box position),
placed inside Layer 1's page shell (#182) and containing Layer 3 content
formats (#122). #184 introduces it as an additive, named unit: number
position moves from being embedded in each build_*_block_tex() output to
being owned by build_content_area_slot_tex(), without changing the existing
build_com_block_tex()/build_com_page_pair() production code path. These
tests exercise the pure-Python builders directly (no pdflatex/lualatex
required).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402


def test_content_area_layout_presets_match_frontend_layout_by_problem_count() -> None:
    # Mirrors frontend/web/src/presetDetail.js's LAYOUT_BY_PROBLEM_COUNT.
    expected = {
        10: (5, 2),
        20: (10, 2),
        30: (10, 3),
    }

    for problem_count, (rows, columns) in expected.items():
        layout = tex_module.CONTENT_AREA_LAYOUT_PRESETS[problem_count]
        assert layout.rows == rows
        assert layout.columns == columns


def test_content_area_layout_accepts_arbitrary_rows_and_columns() -> None:
    layout = tex_module.ContentAreaLayout(rows=7, columns=4)

    assert layout.rows == 7
    assert layout.columns == 4
    assert layout.number_box_width_mm == tex_module.CONTENT_AREA_NUMBER_BOX_WIDTH_MM


def test_build_content_area_slot_tex_places_number_box_before_content() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1)

    slot_tex = tex_module.build_content_area_slot_tex(3, "$1 + 2 = 3$", layout)

    assert slot_tex == "\\makebox[8mm][l]{3)}$1 + 2 = 3$"


def test_build_content_area_slot_tex_uses_layout_number_box_width() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=1, number_box_width_mm=12)

    slot_tex = tex_module.build_content_area_slot_tex(1, "$1 + 1 = 2$", layout)

    assert slot_tex.startswith("\\makebox[12mm][l]{1)}")


def test_build_content_area_tex_composes_one_block_per_slot_in_order() -> None:
    layout = tex_module.ContentAreaLayout(rows=1, columns=2)

    blocks = tex_module.build_content_area_tex(
        indices=[1, 2],
        slot_bodies=["$1 + 1 = 2$", "$2 + 2 = 4$"],
        layout=layout,
    )

    assert blocks == [
        "\\makebox[8mm][l]{1)}$1 + 1 = 2$",
        "\\makebox[8mm][l]{2)}$2 + 2 = 4$",
    ]


def test_build_com_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.ComProblem(index=5, a=3, c=4, target=7)

    content_tex = tex_module.build_com_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 + 4 = 7$"
    assert "5)" not in content_tex


def test_build_com_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_com_block_tex() output byte-for-byte, so
    Layer 2 can be adopted without a visual regression."""
    problem = tex_module.ComProblem(index=5, a=3, c=4, target=7)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_com_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_com_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_ope_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.OpeProblem(index=5, a=3, b=4, operator="add", c=7)

    content_tex = tex_module.build_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 + 4 = 7$"
    assert "5)" not in content_tex


def test_build_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_horizontal_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #205), so Layer 2 can be adopted
    without a visual regression."""
    problem = tex_module.OpeProblem(index=5, a=3, b=4, operator="add", c=7)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_horizontal_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_kuku_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.KukuProblem(index=5, a=3, b=4, c=12)

    content_tex = tex_module.build_kuku_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 \\times 4 = 12$"
    assert "5)" not in content_tex


def test_build_kuku_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_kuku_block_tex() non-reverse output
    byte-for-byte (issue #208), so Layer 2 can be adopted without a visual
    regression."""
    problem = tex_module.KukuProblem(index=5, a=3, b=4, c=12)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_kuku_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_kuku_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_pi_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.PiProblem(index=5, a=3, c=9.42)

    content_tex = tex_module.build_pi_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 \\times 3.14 = 9.42$"
    assert "5)" not in content_tex


def test_build_pi_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_pi_block_tex() non-reverse output
    byte-for-byte (content-format pattern 1a, issue #210), so Layer 2 can be
    adopted without a visual regression."""
    problem = tex_module.PiProblem(index=5, a=3, c=9.42)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_pi_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_pi_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def _make_tree_ope_problem(index: int) -> "tex_module.TreeOpeProblem":
    # (3 + 4) x 2 = 14
    tree = tex_module.ExprTreeNode(
        operator="mul",
        left=tex_module.ExprTreeNode(
            operator="add",
            left=tex_module.ExprTreeNode(value=3),
            right=tex_module.ExprTreeNode(value=4),
        ),
        right=tex_module.ExprTreeNode(value=2),
    )
    return tex_module.TreeOpeProblem(
        index=index, operands=[3, 4, 2], operators=["mul", "add"], tree=tree, result=14,
    )


def test_build_tree_ope_slot_content_tex_omits_problem_number() -> None:
    problem = _make_tree_ope_problem(index=5)

    content_tex = tex_module.build_tree_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$(3 + 4) \\times 2 = 14$"
    assert "5)" not in content_tex


def test_build_tree_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_tree_ope_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #206), so Layer 2 can be adopted
    without a visual regression."""
    problem = _make_tree_ope_problem(index=5)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_tree_ope_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_tree_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_multi_term_ope_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.MultiTermOpeProblem(
        index=5, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=14,
    )

    content_tex = tex_module.build_multi_term_ope_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 + 4 \\times 2 = 14$"
    assert "5)" not in content_tex


def test_build_multi_term_ope_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_multi_term_ope_block_tex() output
    byte-for-byte (content-format pattern 1a, issue #207), so Layer 2 can be
    adopted without a visual regression."""
    problem = tex_module.MultiTermOpeProblem(
        index=5, operands=[3, 4, 2], operators=["add", "mul"], mixed=False, result=14,
    )
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_multi_term_ope_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_multi_term_ope_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_lcm_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.NumberPairProblem(index=5, a=4, b=6, c=12)

    content_tex = tex_module.build_lcm_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$\\mathrm{LCM}(4, 6) = 12$"
    assert "5)" not in content_tex


def test_build_lcm_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_number_pair_block_tex(..., label='LCM')
    output byte-for-byte (issue #211), so Layer 2 can be adopted without a
    visual regression."""
    problem = tex_module.NumberPairProblem(index=5, a=4, b=6, c=12)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_number_pair_block_tex(problem, show_answer=True, label="LCM")
    slot_content_tex = tex_module.build_lcm_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_gcd_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.NumberPairProblem(index=5, a=18, b=24, c=6)

    content_tex = tex_module.build_gcd_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$\\mathrm{GCD}(18, 24) = 6$"
    assert "5)" not in content_tex


def test_build_gcd_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing GCD number-pair block body byte-for-byte (content-
    format pattern 1a, issue #212), so Layer 2 can be adopted without a visual
    regression."""
    problem = tex_module.NumberPairProblem(index=5, a=18, b=24, c=6)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_number_pair_block_tex(
        problem, show_answer=True, label="GCD"
    )
    slot_content_tex = tex_module.build_gcd_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_evenodd_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.EvenOddProblem(index=5, a=4, is_even=True)

    content_tex = tex_module.build_evenodd_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$4 \\Rightarrow \\mathrm{even}$"
    assert "5)" not in content_tex


def test_build_evenodd_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """The Layer-3 body must preserve the existing even/odd TeX output."""
    problem = tex_module.EvenOddProblem(index=5, a=3, is_even=False)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_evenodd_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_evenodd_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_squ_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.SquProblem(index=5, a=3, c=9)

    content_tex = tex_module.build_squ_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$3 \\times 3 = 9$"
    assert "5)" not in content_tex


def test_build_squ_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    """Composing the Layer-2 slot with the number-free Layer-3 content must
    reproduce the existing build_squ_block_tex() output byte-for-byte
    (content-format pattern 1a, issue #209), so Layer 2 can be adopted
    without a visual regression. Only the non-reversed form is covered
    (basic-case scope, matching #199's `com` precedent)."""
    problem = tex_module.SquProblem(index=5, a=3, c=9)
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_squ_block_tex(problem, show_answer=True, reverse=False)
    slot_content_tex = tex_module.build_squ_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"


def test_build_multiples_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.MultiplesProblem(index=5, a=6, multiples=[6, 12, 18, 24])

    content_tex = tex_module.build_multiples_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$6 \\Rightarrow 6, 12, 18, 24$"
    assert "5)" not in content_tex


def test_build_multiples_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = tex_module.MultiplesProblem(index=5, a=6, multiples=[6, 12, 18, 24, 30])
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_multiples_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_multiples_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"
    assert tex_module.build_multiples_slot_content_tex(
        problem, show_answer=False
    ) == f"$6 \\Rightarrow {tex_module.BLANK_ANSWER_TEX}$"


def test_build_divisors_slot_content_tex_omits_problem_number() -> None:
    problem = tex_module.DivisorsProblem(index=5, a=12, divisors=[1, 2, 3, 4, 6, 12])

    content_tex = tex_module.build_divisors_slot_content_tex(problem, show_answer=True)

    assert content_tex == "$12 \\Rightarrow 1, 2, 3, 4, 6, 12$"
    assert "5)" not in content_tex


def test_build_divisors_slot_content_tex_matches_block_tex_body_when_composed() -> None:
    problem = tex_module.DivisorsProblem(index=5, a=12, divisors=[1, 2, 3, 4, 6, 12])
    layout = tex_module.ContentAreaLayout(
        rows=1, columns=1, number_box_width_mm=0
    )

    original_tex = tex_module.build_divisors_block_tex(problem, show_answer=True)
    slot_content_tex = tex_module.build_divisors_slot_content_tex(problem, show_answer=True)
    composed_tex = tex_module.build_content_area_slot_tex(problem.index, slot_content_tex, layout)

    assert composed_tex == f"\\makebox[0mm][l]{{{problem.index})}}{slot_content_tex}"
    assert original_tex == f"{problem.index}) {slot_content_tex}"
    assert tex_module.build_divisors_slot_content_tex(
        problem, show_answer=False
    ) == f"$12 \\Rightarrow {tex_module.BLANK_ANSWER_TEX}$"
