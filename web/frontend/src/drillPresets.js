// Curated mappings from "school grade" to /generate-pdf request params.
// Fraction presets and parenthesized-expression presets (`use_parentheses`)
// are curriculum-aligned and marked latexOnly because the `frac` command and
// `--use-parentheses` flag exist only in nuts_calc_tex.py.

export const GRADES = [1, 2, 3, 4, 5, 6];

export const UNGRADED = 'ungraded';

export const CUSTOM_GRADE = 'custom';

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
    ],
    // Written-calculation (筆算) notation is formally introduced starting
    // grade 2 in the course of study, so grade 1 has no `written` section.
    written: [],
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
        id: 'g4-fraction-common-addsub',
        titleKey: 'preset_g4_fraction_title',
        descKey: 'preset_g4_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['add', 'sub'], numerator_digits: 1,
          denominator_digits: 1, same_denominator: true,
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
        id: 'g5-fraction-unlike-addsub',
        titleKey: 'preset_g5_fraction_title',
        descKey: 'preset_g5_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['add', 'sub'], numerator_digits: 1,
          denominator_digits: 1, different_denominators: true, proper_operands: true,
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
        id: 'g6-fraction-muldiv',
        titleKey: 'preset_g6_fraction_title',
        descKey: 'preset_g6_fraction_desc',
        latexOnly: true,
        params: {
          command_type: 'frac', operator: ['mul', 'div'], numerator_digits: 1,
          denominator_digits: 1, proper_operands: true,
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
  },
};
