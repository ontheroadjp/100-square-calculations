"""
Regression coverage for the "entrance exam prep" (entrance-exam-prep, issue
#73) preset design used by `web/frontend/src/drillPresets.js`'s `examPrep`
entries.

These presets combine `nuts_calc_tex.py`'s `ope --terms`/`--mixed-operators`/
`--use-parentheses` options (issue #71), which have no deterministic
fallback and can raise ValueError for number-range/structure combinations
with too few valid solutions (see
docs/L3_implementation/nuts_calc_tex.py.md's "数値レンジと演算子/構造の組み合わせに
よる ValueError リスクを軽減する設計"). This file exercises the exact
(first-operand digit range, term count, mixed-operators, use-parentheses)
combinations the 27 presets use directly against nuts_calc_tex.py's
generation functions (no pdflatex required) to confirm they don't exhaust
MAX_OPERAND_RETRY_ATTEMPTS in practice.

Keep the (digit range, terms, mixed, parentheses) matrix below in sync with
the `examPrep` preset design in `web/frontend/src/drillPresets.js`.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import nuts_calc_tex as tex_module  # noqa: E402

TRIALS_PER_CONFIG = 20
PROBLEMS_PER_TRIAL = 15

# Mirrors drillPresets.js's a_value: grade4=1 digit, grade5=2 digits,
# grade6=3 digits; b_value stays 1 digit (single-digit) for every grade.
GRADE_FIRST_OPERAND_RANGES = {
    4: (1, 9),
    5: (10, 99),
    6: (100, 999),
}
SECONDARY_OPERAND_RANGE = (1, 9)

STAGE_FLAGS = {
    "basic": (False, False),  # (use_parentheses, mixed_operators)
    "intermediate": (False, True),
    "advanced": (True, True),
}

LEVEL_TERMS = {1: 3, 2: 4, 3: 5}

EXAM_PREP_CONFIGS = [
    pytest.param(grade, stage, level, id=f"g{grade}-examprep-{stage}-{level}")
    for grade in GRADE_FIRST_OPERAND_RANGES
    for stage in STAGE_FLAGS
    for level in LEVEL_TERMS
]


@pytest.mark.parametrize("grade,stage,level", EXAM_PREP_CONFIGS)
def test_exam_prep_preset_config_generates_without_value_error(
    grade: int, stage: str, level: int,
) -> None:
    a_min, a_max = GRADE_FIRST_OPERAND_RANGES[grade]
    b_min, b_max = SECONDARY_OPERAND_RANGE
    use_parentheses, mixed_operators = STAGE_FLAGS[stage]
    terms = LEVEL_TERMS[level]
    nums_a = list(range(a_min, a_max + 1))
    nums_b = list(range(b_min, b_max + 1))

    generate = (
        tex_module.generate_tree_ope_problems
        if use_parentheses
        else tex_module.generate_multi_term_ope_problems
    )

    for _ in range(TRIALS_PER_CONFIG):
        problems = generate(
            nums_a, nums_b, ['mix'], mixed_operators, terms, terms,
            PROBLEMS_PER_TRIAL, 1,
        )
        assert len(problems) == PROBLEMS_PER_TRIAL
