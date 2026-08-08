// Curated mappings from "school grade" to /generate-pdf request params.
// Fraction presets, parenthesized-expression presets (`use_parentheses`),
// decimal presets (`a_decimal_places`/`b_decimal_places`), and int/decimal/
// fraction "mixed" presets are all curriculum-aligned and marked latexOnly
// because the `frac` command, `--use-parentheses` flag, decimal-places
// flags, and `mixed` command all exist only in nuts_calc_tex.py.

export const GRADES = [1, 2, 3, 4, 5, 6];

export const UNGRADED = 'ungraded';

export const CUSTOM_GRADE = 'custom';

// "examPrep" ("中学受験" / entrance-exam prep) presets combine ope's
// --terms/--mixed-operators/--use-parentheses options (issue #71) into 9
// cards per grade (3 stages x 3 levels = 27 total across grades 4-6).
// latexOnly because --terms/--mixed-operators exist only in
// nuts_calc_tex.py. Stage/level parameter choices (first-operand digit
// range per grade, term count per level) mirror
// tests/test_nuts_calc_tex_exam_prep_presets.py, which simulates each
// combination directly against nuts_calc_tex.py's generation functions to
// confirm it doesn't exhaust the retry budget -- keep the two in sync.
const EXAM_PREP_STAGES = [
  { stage: 'basic', mixedOperators: false, useParentheses: false },
  { stage: 'intermediate', mixedOperators: true, useParentheses: false },
  { stage: 'advanced', mixedOperators: true, useParentheses: true },
];

const EXAM_PREP_TERMS_BY_LEVEL = { 1: 3, 2: 4, 3: 5 };

function buildExamPrepPresets(grade, aValue) {
  const presets = [];
  for (const { stage, mixedOperators, useParentheses } of EXAM_PREP_STAGES) {
    for (const level of Object.keys(EXAM_PREP_TERMS_BY_LEVEL)) {
      presets.push({
        id: `g${grade}-examprep-${stage}-${level}`,
        titleKey: `preset_g${grade}_examprep_${stage}_${level}_title`,
        descKey: `preset_g${grade}_examprep_${stage}_${level}_desc`,
        latexOnly: true,
        params: {
          command_type: 'ope',
          operator: ['mix'],
          terms: EXAM_PREP_TERMS_BY_LEVEL[level],
          a_value: aValue,
          b_value: 1,
          ...(mixedOperators && { mixed_operators: true }),
          ...(useParentheses && { use_parentheses: true }),
        },
      });
    }
  }
  return presets;
}

// "written" presets use nuts_calc.py's `--vertical` flag (written-calculation /
// hissan format), which supports 'add'/'sub'/'mul'/'div' (including
// multi-digit-multiplier 'mul', issue #10, and long-division 'div', issue
// #11). 'mix' is intentionally never combined with `vertical: true` here:
// nuts_calc.py rejects that combination but nuts_calc_tex.py does not
// (tracked as a renderer-parity bug, issue #41), so exposing it would behave
// inconsistently depending on which renderer the backend is configured to use.
export const presetsByGrade = {
  1: {
    normal: [
      {
        id: 'g1-add',
        titleKey: 'preset_g1_add_title',
        descKey: 'preset_g1_add_desc',
        params: { command_type: 'ope', operator: ['add'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 },
      },
      {
        id: 'g1-sub',
        titleKey: 'preset_g1_sub_title',
        descKey: 'preset_g1_sub_desc',
        params: { command_type: 'ope', operator: ['sub'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 },
      },
      {
        id: 'g1-addsub',
        titleKey: 'preset_g1_addsub_title',
        descKey: 'preset_g1_addsub_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 },
      },
      {
        id: 'g1-complement10',
        titleKey: 'preset_g1_complement10_title',
        descKey: 'preset_g1_complement10_desc',
        params: { command_type: 'com', a_value: 10 },
      },
      {
        id: 'g1-hyakumasu',
        titleKey: 'preset_g1_hyakumasu_title',
        descKey: 'preset_g1_hyakumasu_desc',
        params: { command_type: '100', a_value: 1, b_value: 1 },
      },
      {
        // No formal square-bracket (□) notation at grade 1 in the course of
        // study; this is an introductory application drill, consistent with
        // grade 1 already having non-standards-mandated presets (e.g.
        // g1-hyakumasu above). latexOnly because --missing-value exists only
        // in nuts_calc_tex.py (issue #69).
        id: 'g1-missing-value',
        titleKey: 'preset_g1_missing_value_title',
        descKey: 'preset_g1_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['add', 'sub'], missing_value: true,
          a_min: 1, a_max: 9, b_min: 1, b_max: 9,
        },
      },
    ],
    // Written-calculation (筆算) notation is formally introduced starting
    // grade 2 in the course of study, so grade 1 has no `written` section.
    written: [],
    // The entrance-exam-prep section only applies to grades 4-6 (see
    // buildExamPrepPresets above).
    examPrep: [],
  },
  2: {
    normal: [
      {
        id: 'g2-add2',
        titleKey: 'preset_g2_add2_title',
        descKey: 'preset_g2_add2_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 2, b_value: 2 },
      },
      {
        id: 'g2-sub2',
        titleKey: 'preset_g2_sub2_title',
        descKey: 'preset_g2_sub2_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 2, b_value: 2 },
      },
      {
        id: 'g2-addsub2',
        titleKey: 'preset_g2_addsub2_title',
        descKey: 'preset_g2_addsub2_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 2, b_value: 2 },
      },
      {
        id: 'g2-kuku',
        titleKey: 'preset_g2_kuku_title',
        descKey: 'preset_g2_kuku_desc',
        params: { command_type: '99' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_dan', min: 1, max: 9, default: 2 },
      },
      {
        id: 'g2-complement100',
        titleKey: 'preset_g2_complement100_title',
        descKey: 'preset_g2_complement100_desc',
        params: { command_type: 'com', a_value: 100 },
      },
      {
        // Matches the formal grade-2 course-of-study unit A(3) 加法と減法との
        // 相互関係 (elementary-course-of-study-mathematics-2017.pdf p.114),
        // e.g. □＋５＝12. latexOnly because --missing-value exists only in
        // nuts_calc_tex.py (issue #69).
        id: 'g2-missing-value',
        titleKey: 'preset_g2_missing_value_title',
        descKey: 'preset_g2_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['add', 'sub'], missing_value: true,
          a_value: 2, b_value: 2,
        },
      },
    ],
    written: [
      {
        id: 'g2-add-written',
        titleKey: 'preset_g2_add_written_title',
        descKey: 'preset_g2_add_written_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 2, b_value: 2, vertical: true },
      },
      {
        id: 'g2-sub-written',
        titleKey: 'preset_g2_sub_written_title',
        descKey: 'preset_g2_sub_written_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 2, b_value: 2, vertical: true },
      },
      {
        id: 'g2-addsub-written',
        titleKey: 'preset_g2_addsub_written_title',
        descKey: 'preset_g2_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 2, b_value: 2, vertical: true },
      },
    ],
    examPrep: [],
  },
  3: {
    normal: [
      {
        id: 'g3-mul',
        titleKey: 'preset_g3_mul_title',
        descKey: 'preset_g3_mul_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1 },
      },
      {
        id: 'g3-div',
        titleKey: 'preset_g3_div_title',
        descKey: 'preset_g3_div_desc',
        params: { command_type: 'ope', operator: ['div'], a_value: 2, b_value: 1 },
      },
      {
        id: 'g3-add3',
        titleKey: 'preset_g3_add3_title',
        descKey: 'preset_g3_add3_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 3, b_value: 3 },
      },
      {
        id: 'g3-sub3',
        titleKey: 'preset_g3_sub3_title',
        descKey: 'preset_g3_sub3_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 3, b_value: 3 },
      },
      {
        id: 'g3-addsub3',
        titleKey: 'preset_g3_addsub3_title',
        descKey: 'preset_g3_addsub3_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 3, b_value: 3 },
      },
      {
        id: 'g3-mul-intermediate',
        titleKey: 'preset_g3_mul_intermediate_title',
        descKey: 'preset_g3_mul_intermediate_desc',
        // operator is pinned to ['mul'] (not left to default) because
        // nuts_calc_tex.py rejects --intermediate with any other operator,
        // while nuts_calc.py silently ignores it -- being explicit keeps the
        // request valid on both renderers (see issue #42).
        params: { command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1, intermediate: true },
      },
      {
        // Matches the formal grade-3 course-of-study unit covering □ for
        // multiplication/division relationships (elementary-course-of-study
        // -mathematics-2017.pdf p.55), e.g. 12÷3 framed as 3×□＝12. latexOnly
        // because --missing-value exists only in nuts_calc_tex.py (issue #69).
        id: 'g3-missing-value',
        titleKey: 'preset_g3_missing_value_title',
        descKey: 'preset_g3_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mul', 'div'], missing_value: true,
          a_value: 2, b_value: 1,
        },
      },
      {
        id: 'g3-fraction-simple-addsub',
        titleKey: 'preset_g3_fraction_title',
        descKey: 'preset_g3_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['add', 'sub'], numerator_digits: 1,
          denominator_digits: 1, same_denominator: true, proper_operands: true,
          proper_result: true,
        },
      },
      {
        // Matches the formal grade-3 course-of-study unit A(5) 小数の意味と表し方
        // (elementary-course-of-study-mathematics-2017.pdf p.156): simple
        // one-decimal-place (1/10 unit) addition/subtraction. latexOnly
        // because --a-decimal-places/--b-decimal-places exist only in
        // nuts_calc_tex.py (issue #76).
        id: 'g3-decimal-addsub',
        titleKey: 'preset_g3_decimal_addsub_title',
        descKey: 'preset_g3_decimal_addsub_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['add', 'sub'], a_value: 1, b_value: 1,
          a_decimal_places: 1, b_decimal_places: 1,
        },
      },
    ],
    written: [
      {
        id: 'g3-add-written',
        titleKey: 'preset_g3_add_written_title',
        descKey: 'preset_g3_add_written_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 3, b_value: 3, vertical: true },
      },
      {
        id: 'g3-sub-written',
        titleKey: 'preset_g3_sub_written_title',
        descKey: 'preset_g3_sub_written_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 3, b_value: 3, vertical: true },
      },
      {
        id: 'g3-addsub-written',
        titleKey: 'preset_g3_addsub_written_title',
        descKey: 'preset_g3_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 3, b_value: 3, vertical: true },
      },
      {
        id: 'g3-mul-written',
        titleKey: 'preset_g3_mul_written_title',
        descKey: 'preset_g3_mul_written_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1, vertical: true },
      },
    ],
    examPrep: [],
  },
  4: {
    normal: [
      {
        id: 'g4-mul',
        titleKey: 'preset_g4_mul_title',
        descKey: 'preset_g4_mul_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 3, b_value: 2 },
      },
      {
        id: 'g4-div',
        titleKey: 'preset_g4_div_title',
        descKey: 'preset_g4_div_desc',
        params: { command_type: 'ope', operator: ['div'], a_value: 3, b_value: 2 },
      },
      {
        id: 'g4-mix',
        titleKey: 'preset_g4_mix_title',
        descKey: 'preset_g4_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 2, b_value: 2 },
      },
      {
        // Matches the formal grade-4 course-of-study unit A(6) 数量の関係を表す式
        // ("四則の混合した式や（　）を用いた式", elementary-course-of-study
        // -mathematics-2017.pdf page 196): single-digit three-operand
        // expressions. operator: ['mix'] plus --use-parentheses's own
        // per-problem position/operator randomization (nuts_calc_tex.py
        // issue #67) varies both which pair is parenthesized ("(a op b) op
        // c" vs "a op (b op c)") and which of the four operations are used,
        // instead of a single fixed pattern. latexOnly because
        // --use-parentheses exists only in nuts_calc_tex.py.
        id: 'g4-parentheses',
        titleKey: 'preset_g4_parentheses_title',
        descKey: 'preset_g4_parentheses_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], use_parentheses: true,
          a_value: 1, b_value: 1,
        },
      },
      {
        // Extends the g4-mix preset (2-digit, mixed operators) with
        // --missing-value's boxed-blank treatment: grade 4 formalizes □/△
        // notation for mixed-operator expressions. latexOnly because
        // --missing-value exists only in nuts_calc_tex.py (issue #69).
        id: 'g4-missing-value',
        titleKey: 'preset_g4_missing_value_title',
        descKey: 'preset_g4_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], missing_value: true,
          a_value: 2, b_value: 2,
        },
      },
      {
        id: 'g4-fraction-common-addsub',
        titleKey: 'preset_g4_fraction_title',
        descKey: 'preset_g4_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['add', 'sub'], numerator_digits: 1,
          denominator_digits: 1, same_denominator: true,
        },
      },
      {
        // Matches the formal grade-4 course-of-study unit A(4) 小数の仕組みと
        // その計算 (elementary-course-of-study-mathematics-2017.pdf p.196):
        // multi-place (1/100 unit) decimal addition/subtraction. latexOnly
        // because --a-decimal-places/--b-decimal-places exist only in
        // nuts_calc_tex.py (issue #76).
        id: 'g4-decimal-addsub',
        titleKey: 'preset_g4_decimal_addsub_title',
        descKey: 'preset_g4_decimal_addsub_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['add', 'sub'], a_value: 3, b_value: 3,
          a_decimal_places: 2, b_decimal_places: 2,
        },
      },
      {
        // Same course-of-study unit (p.196): "乗数や除数が整数である場合の
        // 小数の乗法" (decimal x integer). b_decimal_places is left at its
        // default (0) so the second operand is a plain integer -- the
        // asymmetric decimal-places case nuts_calc_tex.py restricts to a
        // single mul/div operator (issue #76).
        id: 'g4-decimal-mul',
        titleKey: 'preset_g4_decimal_mul_title',
        descKey: 'preset_g4_decimal_mul_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1,
          a_decimal_places: 1,
        },
      },
      {
        // Same unit (p.196): "...小数の除法" (decimal / integer).
        id: 'g4-decimal-div',
        titleKey: 'preset_g4_decimal_div_title',
        descKey: 'preset_g4_decimal_div_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['div'], a_value: 2, b_value: 1,
          a_decimal_places: 1,
        },
      },
    ],
    written: [
      {
        id: 'g4-mul-written',
        titleKey: 'preset_g4_mul_written_title',
        descKey: 'preset_g4_mul_written_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 3, b_value: 2, vertical: true },
      },
      {
        id: 'g4-div-written',
        titleKey: 'preset_g4_div_written_title',
        descKey: 'preset_g4_div_written_desc',
        params: { command_type: 'ope', operator: ['div'], a_value: 3, b_value: 2, vertical: true },
      },
      {
        id: 'g4-add-written',
        titleKey: 'preset_g4_add_written_title',
        descKey: 'preset_g4_add_written_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 4, b_value: 4, vertical: true },
      },
      {
        id: 'g4-sub-written',
        titleKey: 'preset_g4_sub_written_title',
        descKey: 'preset_g4_sub_written_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 4, b_value: 4, vertical: true },
      },
      {
        id: 'g4-addsub-written',
        titleKey: 'preset_g4_addsub_written_title',
        descKey: 'preset_g4_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 4, b_value: 4, vertical: true },
      },
    ],
    examPrep: buildExamPrepPresets(4, 1),
  },
  5: {
    normal: [
      {
        id: 'g5-pi',
        titleKey: 'preset_g5_pi_title',
        descKey: 'preset_g5_pi_desc',
        params: { command_type: 'pi' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
      {
        id: 'g5-mix',
        titleKey: 'preset_g5_mix_title',
        descKey: 'preset_g5_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 3, b_value: 2 },
      },
      {
        // Advanced extension of g4-parentheses: no grade-5 course-of-study
        // unit covers this directly (that unit is grade 4 only), so this is
        // an ungraded-in-spirit but grade-5-placed application drill with a
        // 2-digit first operand (b/c stay single-digit -- verified by
        // simulation that widening both b and c to 2 digits makes some
        // operator/position combinations, e.g. sub outside a mul on the
        // right, have essentially no solvable triple in range). Same
        // operator/position randomization as g4-parentheses.
        id: 'g5-parentheses-advanced',
        titleKey: 'preset_g5_parentheses_advanced_title',
        descKey: 'preset_g5_parentheses_advanced_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], use_parentheses: true,
          a_value: 2, b_value: 1,
        },
      },
      {
        // Extends the g5-mix preset (3-digit x 2-digit, mixed operators)
        // with --missing-value's boxed-blank treatment. No direct
        // course-of-study unit for this combination; same "advanced
        // application" framing as g5-parentheses-advanced. latexOnly
        // because --missing-value exists only in nuts_calc_tex.py (issue
        // #69).
        id: 'g5-missing-value',
        titleKey: 'preset_g5_missing_value_title',
        descKey: 'preset_g5_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], missing_value: true,
          a_value: 3, b_value: 2,
        },
      },
      {
        id: 'g5-fraction-unlike-addsub',
        titleKey: 'preset_g5_fraction_title',
        descKey: 'preset_g5_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['add', 'sub'], numerator_digits: 1,
          denominator_digits: 1, different_denominators: true, proper_operands: true,
        },
      },
      {
        // Matches the formal grade-5 course-of-study unit covering "小数の
        // 乗法，除法の意味" (elementary-course-of-study-mathematics-2017.pdf
        // p.245): decimal x decimal. Both operands use the same
        // decimal-places value (1), which nuts_calc_tex.py requires for
        // 'mul' to keep the product within elementary-school-appropriate
        // range (issue #76).
        id: 'g5-decimal-mul',
        titleKey: 'preset_g5_decimal_mul_title',
        descKey: 'preset_g5_decimal_mul_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 2,
          a_decimal_places: 1, b_decimal_places: 1,
        },
      },
      {
        // Same unit (p.245): decimal / decimal. Equal decimal places make
        // the quotient an exact whole number (aligning decimal points before
        // dividing, as taught in the course of study) -- never a
        // repeating/infinite decimal, since nuts_calc_tex.py's decimal
        // division always reuses the exact-integer-division guarantee (see
        // nuts_calc_tex.py.md's decimal-arithmetic design note).
        id: 'g5-decimal-div',
        titleKey: 'preset_g5_decimal_div_title',
        descKey: 'preset_g5_decimal_div_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['div'], a_value: 2, b_value: 2,
          a_decimal_places: 1, b_decimal_places: 1,
        },
      },
    ],
    written: [
      {
        id: 'g5-add-written',
        titleKey: 'preset_g5_add_written_title',
        descKey: 'preset_g5_add_written_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 5, b_value: 5, vertical: true },
      },
      {
        id: 'g5-sub-written',
        titleKey: 'preset_g5_sub_written_title',
        descKey: 'preset_g5_sub_written_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 5, b_value: 5, vertical: true },
      },
      {
        id: 'g5-addsub-written',
        titleKey: 'preset_g5_addsub_written_title',
        descKey: 'preset_g5_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 5, b_value: 5, vertical: true },
      },
    ],
    examPrep: buildExamPrepPresets(5, 2),
  },
  6: {
    normal: [
      {
        id: 'g6-pi',
        titleKey: 'preset_g6_pi_title',
        descKey: 'preset_g6_pi_desc',
        params: { command_type: 'pi' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
      {
        id: 'g6-mix',
        titleKey: 'preset_g6_mix_title',
        descKey: 'preset_g6_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 3, b_value: 3 },
      },
      {
        // Advanced extension of g4-parentheses (see g5-parentheses-advanced):
        // a 3-digit first operand (one step up from grade 5's 2-digit) is
        // the differentiator, with b/c kept single-digit for the same
        // solvability reason as g5-parentheses-advanced. Same
        // operator/position randomization as g4-parentheses.
        id: 'g6-parentheses-advanced',
        titleKey: 'preset_g6_parentheses_advanced_title',
        descKey: 'preset_g6_parentheses_advanced_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], use_parentheses: true,
          a_value: 3, b_value: 1,
        },
      },
      {
        // Extends the g6-mix preset (same operand ranges) with
        // --missing-value's boxed-blank treatment. Same "advanced
        // application" framing as g6-parentheses-advanced. latexOnly
        // because --missing-value exists only in nuts_calc_tex.py (issue
        // #69).
        id: 'g6-missing-value',
        titleKey: 'preset_g6_missing_value_title',
        descKey: 'preset_g6_missing_value_desc',
        latexOnly: true,
        params: {
          command_type: 'ope', operator: ['mix'], missing_value: true,
          a_value: 3, b_value: 3,
        },
      },
      {
        id: 'g6-fraction-muldiv',
        titleKey: 'preset_g6_fraction_title',
        descKey: 'preset_g6_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['mul', 'div'], numerator_digits: 1,
          denominator_digits: 1, proper_operands: true,
        },
      },
      {
        // Matches the formal grade-6 course-of-study "内容の取扱い" note on
        // 分数の乗法，除法 (elementary-course-of-study-mathematics-2017.pdf
        // p.293): "整数や小数の乗法や除法を分数の場合の計算にまとめることも
        // 取り扱うものとする" (integer/decimal multiplication and division
        // shall also be handled by unifying them into fraction-form
        // calculation) -- worked example on p.294: "5÷2×0.3" converted to a
        // fraction product. The `mixed` command (nuts_calc_tex.py, issue
        // #76) implements exactly this: int/decimal/fraction operands,
        // computed exactly via fractions.Fraction and always answered as a
        // fraction (never decimal notation), so a division whose quotient
        // doesn't terminate (e.g. 2/3) is still exact, not an
        // infinite/repeating decimal. latexOnly because the `mixed` command
        // exists only in nuts_calc_tex.py.
        id: 'g6-mixed-basic',
        titleKey: 'preset_g6_mixed_basic_title',
        descKey: 'preset_g6_mixed_basic_desc',
        latexOnly: true,
        params: {
          command_type: 'mixed', operator: ['mix'], terms: 2,
          numerator_digits: 1, denominator_digits: 1, decimal_places: 1,
          a_kind: ['int', 'decimal', 'fraction'], b_kind: ['int', 'decimal', 'fraction'],
        },
      },
      {
        // Same course-of-study basis as g6-mixed-basic, extended to a
        // 3-term chained expression (matching the p.294 worked example's
        // shape, "5÷2×0.3") via --mixed-operators (standard * / precedence
        // over + -, nuts_calc_tex.py issue #71/#76).
        id: 'g6-mixed-advanced',
        titleKey: 'preset_g6_mixed_advanced_title',
        descKey: 'preset_g6_mixed_advanced_desc',
        latexOnly: true,
        params: {
          command_type: 'mixed', operator: ['mix'], terms: 3, mixed_operators: true,
          numerator_digits: 1, denominator_digits: 1, decimal_places: 1,
          a_kind: ['int', 'decimal', 'fraction'], b_kind: ['int', 'decimal', 'fraction'],
        },
      },
    ],
    written: [
      {
        id: 'g6-add-written',
        titleKey: 'preset_g6_add_written_title',
        descKey: 'preset_g6_add_written_desc',
        params: { command_type: 'ope', operator: ['add'], a_value: 5, b_value: 3, vertical: true },
      },
      {
        id: 'g6-sub-written',
        titleKey: 'preset_g6_sub_written_title',
        descKey: 'preset_g6_sub_written_desc',
        params: { command_type: 'ope', operator: ['sub'], a_value: 5, b_value: 3, vertical: true },
      },
      {
        id: 'g6-addsub-written',
        titleKey: 'preset_g6_addsub_written_title',
        descKey: 'preset_g6_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 5, b_value: 3, vertical: true },
      },
    ],
    examPrep: buildExamPrepPresets(6, 3),
  },
  // Drills that don't correspond to any single course-of-study grade unit
  // (unlike e.g. `pi`, which is anchored to grade 5's introduction of the
  // 3.14 constant): `aBc` is a mental-math decomposition trick and `squ` is
  // a generic same-number multiplication drill, neither taught as a named
  // elementary-school unit. Neither has a `--vertical` form (only `ope`
  // supports it), so `written` stays empty. Keyed by `UNGRADED` so
  // `GradeDrills.jsx` can look it up the same way as a numbered grade.
  [UNGRADED]: {
    normal: [
      {
        id: 'ungraded-abc',
        titleKey: 'preset_ungraded_abc_title',
        descKey: 'preset_ungraded_abc_desc',
        params: { command_type: 'aBc' },
      },
      {
        id: 'ungraded-squ',
        titleKey: 'preset_ungraded_squ_title',
        descKey: 'preset_ungraded_squ_desc',
        params: { command_type: 'squ' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
    ],
    written: [],
    examPrep: [],
  },
};
