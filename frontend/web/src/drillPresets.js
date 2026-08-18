// Grade -> category -> menu-item hierarchy matching
// docs/uiux/calculation_drill_menu_parameters_v1.md exactly (issue #98).
//
// Every menu item carries:
// - settings: the doc's 固有設定/選択可能値 as either a `choice` (segmented
//   control) or a `fixed` (displayed, not editable) setting, per the doc's
//   "UI実装上のルール".
// - buildParams(state): maps a settings-state object (one entry per
//   `choice` setting id) to a POST /generate-pdf request body.
// - supportLevel: 'full' (nuts_calc_tex.py honors every setting), 'partial'
//   (it generates correct problems for the item but can't honor one or more
//   settings -- see the linked issue in the comment above each affected
//   item), or 'none' (no backend support at all; unused as of #98, since
//   #91-#96 closed all commands the doc requires).
//
// All items are latexOnly: nuts_calc_tex.py-only flags (carry_mode,
// remainder_mode, decimal places, terms/mixed-operators, frac/mixed/compare
// and the number-theory commands) cover essentially every doc item; the
// handful of plain ope/'99' items work on both renderers but are still
// marked latexOnly for consistency with canUsePreset's renderer gate, since
// mixing gate semantics per item would complicate catalog.js/preset.js's
// canUseItem for no practical benefit (frontend/web only ever runs against
// one active renderer at a time, selected server-side via
// NUTS_CALC_RENDERER).

export const GRADES = [1, 2, 3, 4, 5, 6];

export const UNGRADED = 'ungraded';

const OPT_NONE = { value: 'none', labelKey: 'setting_option_none' };
const OPT_REQUIRED = { value: 'required', labelKey: 'setting_option_required' };
const OPT_MIXED = { value: 'mixed', labelKey: 'setting_option_mixed', hintKey: 'setting_mixed_hint' };

function carrySetting(labelKey) {
  return { id: 'carryMode', labelKey, type: 'choice', options: [OPT_NONE, OPT_REQUIRED, OPT_MIXED], default: 'mixed' };
}

function remainderSetting(labelKey) {
  return { id: 'remainderMode', labelKey, type: 'choice', options: [OPT_NONE, OPT_REQUIRED, OPT_MIXED], default: 'mixed' };
}

function fixedSetting(id, labelKey, valueLabelKey) {
  return { id, labelKey, type: 'fixed', valueLabelKey };
}

// nuts_calc_tex.py rejects --mixed-carry-borrow unless -o includes both
// add and sub (single-operator "mixed" carry has no dedicated flag); for a
// single-operator item, 'mixed' is achieved by omitting carry_mode
// entirely, which leaves carrying unconstrained the same way.
function carryModeField(operator, state) {
  const mode = state?.carryMode ?? 'mixed';
  if (mode === 'mixed' && operator.length < 2) return {};
  return { carry_mode: mode };
}

function remainderModeParam(state) {
  return state?.remainderMode ?? 'mixed';
}

// nuts_calc_tex.py's --require-reducible/--no-reducible/--mixed-reducible
// (#114) has no single-operator restriction (unlike carryModeField above),
// so 'mixed' is always sent through explicitly, mirroring
// remainderModeParam rather than carryModeField.
function reducibleModeParam(state) {
  return state?.reduction ?? 'mixed';
}

// Builds an examplesFor(settingsState) for a menu item's example chips: looks
// up the example set for the current combination of the given setting ids
// (joined with "_", e.g. ['denominator', 'numberKind'] -> "same_fraction").
// The all-'mixed' combination must always be present in byCombo; it is used
// both for that combination and as the fallback for any unset/unrecognized
// value, so it stays identical to the item's own static `examples` (every
// affected setting here defaults to 'mixed').
function examplesByChoice(settingIds, byCombo) {
  const mixedKey = settingIds.map(() => 'mixed').join('_');
  return (settingsState) => {
    const key = settingIds.map((id) => settingsState?.[id] ?? 'mixed').join('_');
    return byCombo[key] ?? byCombo[mixedKey];
  };
}

// ---------------------------------------------------------------------
// Grade 1
// ---------------------------------------------------------------------

const grade1 = {
  addition: [
    {
      id: 'g1-add-10',
      titleKey: 'menu_g1_add_10_title',
      descKey: 'menu_g1_add_10_desc',
      pointKey: 'menu_g1_add_10_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3+5', '6+4', '2+6'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], carry_mode: 'none',
        a_min: 1, a_max: 9, b_min: 1, b_max: 9, result_max: 10,
      }),
    },
    {
      id: 'g1-add-20',
      titleKey: 'menu_g1_add_20_title',
      descKey: 'menu_g1_add_20_desc',
      pointKey: 'menu_g1_add_20_point',
      difficultyKey: 'difficulty_standard',
      examples: ['8+7', '9+6', '5+8'],
      settings: [fixedSetting('carryMode', 'setting_carry_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], carry_mode: 'required',
        a_min: 1, a_max: 9, b_min: 1, b_max: 9, result_max: 20,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g1-sub-10',
      titleKey: 'menu_g1_sub_10_title',
      descKey: 'menu_g1_sub_10_desc',
      pointKey: 'menu_g1_sub_10_point',
      difficultyKey: 'difficulty_basic',
      examples: ['8-3', '10-6', '9-4'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'],
        a_min: 2, a_max: 10, b_min: 1, b_max: 9, result_max: 10,
      }),
    },
    {
      id: 'g1-sub-20',
      titleKey: 'menu_g1_sub_20_title',
      descKey: 'menu_g1_sub_20_desc',
      pointKey: 'menu_g1_sub_20_point',
      difficultyKey: 'difficulty_standard',
      examples: ['13-7', '16-9', '15-8'],
      settings: [fixedSetting('carryMode', 'setting_borrow_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'], carry_mode: 'required',
        a_min: 10, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
      }),
    },
  ],
  'four-operations': [
    {
      id: 'g1-three-terms',
      titleKey: 'menu_g1_three_terms_title',
      descKey: 'menu_g1_three_terms_desc',
      pointKey: 'menu_g1_three_terms_point',
      difficultyKey: 'difficulty_advanced',
      examples: ['3+4+2', '8-3+4', '5+3-4'],
      settings: [
        {
          id: 'operators', labelKey: 'setting_operators_label', type: 'choice',
          options: [
            { value: 'add', labelKey: 'setting_option_add_only' },
            { value: 'addsub', labelKey: 'setting_option_addsub_mixed' },
          ],
          default: 'addsub',
        },
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => {
        const addOnly = (state?.operators ?? 'addsub') === 'add';
        return {
          command_type: 'ope',
          operator: addOnly ? ['add'] : ['add', 'sub'],
          terms: 3,
          ...(!addOnly && { mixed_operators: true }),
          a_min: 1, a_max: 9, b_min: 1, b_max: 9,
        };
      },
    },
  ],
};

// ---------------------------------------------------------------------
// Grade 2
// ---------------------------------------------------------------------

const grade2 = {
  addition: [
    {
      id: 'g2-add-2digit',
      titleKey: 'menu_g2_add_2digit_title',
      descKey: 'menu_g2_add_2digit_desc',
      pointKey: 'menu_g2_add_2digit_point',
      difficultyKey: 'difficulty_basic',
      examples: ['34+5', '7+26', '42+35'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['34+5', '42+35', '61+7'],
        required: ['7+26', '48+37', '19+45'],
        mixed: ['34+5', '7+26', '42+35'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 99, b_min: 1, b_max: 99, result_max: 100,
      }),
    },
    {
      id: 'g2-add-result-1000',
      titleKey: 'menu_g2_add_result_1000_title',
      descKey: 'menu_g2_add_result_1000_desc',
      pointKey: 'menu_g2_add_result_1000_point',
      difficultyKey: 'difficulty_advanced',
      examples: ['625+75', '999+1', '321+456'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['321+456', '102+304', '210+369'],
        required: ['625+75', '999+1', '267+458'],
        mixed: ['625+75', '999+1', '321+456'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 999, b_min: 1, b_max: 999, result_max: 1000,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g2-sub-2digit',
      titleKey: 'menu_g2_sub_2digit_title',
      descKey: 'menu_g2_sub_2digit_desc',
      pointKey: 'menu_g2_sub_2digit_point',
      difficultyKey: 'difficulty_basic',
      examples: ['38-5', '32-7', '72-48'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['38-5', '95-23', '76-24'],
        required: ['32-7', '72-48', '61-38'],
        mixed: ['38-5', '32-7', '72-48'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 10, a_max: 99, b_min: 1, b_max: 99, result_max: 100,
      }),
    },
    {
      id: 'g2-sub-result-1000',
      titleKey: 'menu_g2_sub_result_1000_title',
      descKey: 'menu_g2_sub_result_1000_desc',
      pointKey: 'menu_g2_sub_result_1000_point',
      difficultyKey: 'difficulty_advanced',
      examples: ['500-125', '302-158', '456-321'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['456-321', '864-521', '789-456'],
        required: ['500-125', '302-158', '423-186'],
        mixed: ['500-125', '302-158', '456-321'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 1, a_max: 999, b_min: 1, b_max: 999, result_max: 1000,
      }),
    },
  ],
  multiplication: [
    {
      id: 'g2-kuku',
      titleKey: 'menu_g2_kuku_title',
      descKey: 'menu_g2_kuku_desc',
      pointKey: 'menu_g2_kuku_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3×7', '8×6', '5×9'],
      examplesFor: (state) => {
        const dan = state?.dan ?? 'mixed';
        if (dan === 'mixed') return ['3×7', '8×6', '5×9'];
        const examplesByOrder = {
          ascending: [`${dan}×1`, `${dan}×2`, `${dan}×3`],
          descending: [`${dan}×9`, `${dan}×8`, `${dan}×7`],
          random: [`${dan}×6`, `${dan}×3`, `${dan}×8`],
        };
        return examplesByOrder[state?.questionOrder ?? 'ascending'] ?? examplesByOrder.ascending;
      },
      settings: [
        {
          id: 'dan', labelKey: 'setting_dan_label', type: 'choice',
          options: [
            { value: '1', labelKey: 'setting_option_dan_1' },
            { value: '2', labelKey: 'setting_option_dan_2' },
            { value: '3', labelKey: 'setting_option_dan_3' },
            { value: '4', labelKey: 'setting_option_dan_4' },
            { value: '5', labelKey: 'setting_option_dan_5' },
            { value: '6', labelKey: 'setting_option_dan_6' },
            { value: '7', labelKey: 'setting_option_dan_7' },
            { value: '8', labelKey: 'setting_option_dan_8' },
            { value: '9', labelKey: 'setting_option_dan_9' },
            { value: 'mixed', labelKey: 'setting_option_mixed', hintKey: 'setting_mixed_hint' },
          ],
          default: 'mixed',
        },
        {
          id: 'questionOrder', labelKey: 'setting_question_order_label', type: 'choice',
          options: [
            { value: 'ascending', labelKey: 'setting_option_order_ascending' },
            { value: 'descending', labelKey: 'setting_option_order_descending' },
            { value: 'random', labelKey: 'setting_option_order_random' },
          ],
          default: 'ascending',
          disabledWhen: (state) => state?.dan === 'mixed',
          resolveValue: (state) => (state?.dan === 'mixed' ? 'random' : (state?.questionOrder ?? 'ascending')),
        },
      ],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: (state) => {
        const dan = state?.dan ?? 'mixed';
        if (dan === 'mixed') {
          return { command_type: 'ope', operator: ['mul'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 };
        }
        const params = { command_type: '99', a_value: Number(dan) };
        const questionOrder = state?.questionOrder ?? 'ascending';
        if (questionOrder === 'descending') params.descend = true;
        if (questionOrder === 'random') params.shuffle = true;
        return params;
      },
    },
  ],
  'four-operations': [
    {
      id: 'g2-addsub-mixed',
      titleKey: 'menu_g2_addsub_mixed_title',
      descKey: 'menu_g2_addsub_mixed_desc',
      pointKey: 'menu_g2_addsub_mixed_point',
      difficultyKey: 'difficulty_standard',
      examples: ['35+24-18', '46-15+22', '18+37-9'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_addsub_mixed')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub'], terms: 3, mixed_operators: true,
        a_min: 1, a_max: 99, b_min: 1, b_max: 99,
      }),
    },
    {
      id: 'g2-parentheses',
      titleKey: 'menu_g2_parentheses_title',
      descKey: 'menu_g2_parentheses_desc',
      pointKey: 'menu_g2_parentheses_point',
      difficultyKey: 'difficulty_standard',
      examples: ['35-(12+8)', '52-(23+9)', '68-(15+22)'],
      settings: [fixedSetting('parentheses', 'setting_parentheses_label', 'setting_option_present')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub'], terms: 3, use_parentheses: true,
        a_min: 1, a_max: 90, b_min: 1, b_max: 90,
      }),
    },
  ],
};

// ---------------------------------------------------------------------
// Grade 3
// ---------------------------------------------------------------------

const grade3 = {
  addition: [
    {
      id: 'g3-add-result-10000',
      titleKey: 'menu_g3_add_result_10000_title',
      descKey: 'menu_g3_add_result_10000_desc',
      pointKey: 'menu_g3_add_result_10000_point',
      difficultyKey: 'difficulty_advanced',
      examples: ['6250+750', '9999+1', '3210+4560'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['1234+5000', '3210+4560', '4123+5641'],
        required: ['6250+750', '9999+1', '3456+2789'],
        mixed: ['6250+750', '9999+1', '3210+4560'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 9999, b_min: 1, b_max: 9999, result_max: 10000,
      }),
    },
    {
      id: 'g3-decimal-addsub',
      titleKey: 'menu_g3_decimal_addsub_title',
      descKey: 'menu_g3_decimal_addsub_desc',
      pointKey: 'menu_g3_decimal_addsub_point',
      difficultyKey: 'difficulty_basic',
      examples: ['2.4+3.1', '4.7+1.6', '5.2+3.6'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['2.4+3.1', '5.2+3.6', '1.3+4.5'],
        required: ['4.7+1.6', '3.8+2.5', '6.9+1.4'],
        mixed: ['2.4+3.1', '4.7+1.6', '5.2+3.6'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], a_value: 1, b_value: 1,
        a_decimal_places: 1, b_decimal_places: 1, ...carryModeField(['add'], state),
      }),
    },
    {
      id: 'g3-fraction-add',
      titleKey: 'menu_g3_fraction_add_title',
      descKey: 'menu_g3_fraction_add_desc',
      pointKey: 'menu_g3_fraction_add_point',
      difficultyKey: 'difficulty_basic',
      examples: ['2/7+3/7', '1/9+4/9', '3/8+2/8'],
      settings: [fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['add'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, proper_operands: true, proper_result: true,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g3-sub-result-10000',
      titleKey: 'menu_g3_sub_result_10000_title',
      descKey: 'menu_g3_sub_result_10000_desc',
      pointKey: 'menu_g3_sub_result_10000_point',
      difficultyKey: 'difficulty_advanced',
      examples: ['5000-1250', '3020-1580', '4560-3210'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['4560-3210', '8640-5210', '7531-6420'],
        required: ['5000-1250', '3020-1580', '4021-1876'],
        mixed: ['5000-1250', '3020-1580', '4560-3210'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 1, a_max: 9999, b_min: 1, b_max: 9999, result_max: 10000,
      }),
    },
    {
      id: 'g3-decimal-sub',
      titleKey: 'menu_g3_decimal_sub_title',
      descKey: 'menu_g3_decimal_sub_desc',
      pointKey: 'menu_g3_decimal_sub_point',
      difficultyKey: 'difficulty_basic',
      examples: ['5.7-2.3', '8.4-3.9', '6.8-2.5'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['5.7-2.3', '6.8-2.5', '9.6-3.2'],
        required: ['8.4-3.9', '5.2-1.7', '7.3-2.8'],
        mixed: ['5.7-2.3', '8.4-3.9', '6.8-2.5'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], a_value: 1, b_value: 1,
        a_decimal_places: 1, b_decimal_places: 1, ...carryModeField(['sub'], state),
      }),
    },
    {
      id: 'g3-fraction-sub',
      titleKey: 'menu_g3_fraction_sub_title',
      descKey: 'menu_g3_fraction_sub_desc',
      pointKey: 'menu_g3_fraction_sub_point',
      difficultyKey: 'difficulty_basic',
      examples: ['6/7-2/7', '5/8-3/8', '7/9-4/9'],
      settings: [fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['sub'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, proper_operands: true, proper_result: true,
      }),
    },
  ],
  multiplication: [
    {
      id: 'g3-mul-2x1',
      titleKey: 'menu_g3_mul_2x1_title',
      descKey: 'menu_g3_mul_2x1_desc',
      pointKey: 'menu_g3_mul_2x1_point',
      difficultyKey: 'difficulty_basic',
      examples: ['38×7', '24×5', '56×3'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1 }),
    },
    {
      id: 'g3-mul-3x1',
      titleKey: 'menu_g3_mul_3x1_title',
      descKey: 'menu_g3_mul_3x1_desc',
      pointKey: 'menu_g3_mul_3x1_point',
      difficultyKey: 'difficulty_standard',
      examples: ['326×4', '425×7', '218×6'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'ope', operator: ['mul'], a_value: 3, b_value: 1 }),
    },
    {
      id: 'g3-mul-2x2',
      titleKey: 'menu_g3_mul_2x2_title',
      descKey: 'menu_g3_mul_2x2_desc',
      pointKey: 'menu_g3_mul_2x2_point',
      difficultyKey: 'difficulty_standard',
      examples: ['47×23', '34×28', '52×19'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 2 }),
    },
  ],
  division: [
    {
      id: 'g3-div-kuku',
      titleKey: 'menu_g3_div_kuku_title',
      descKey: 'menu_g3_div_kuku_desc',
      pointKey: 'menu_g3_div_kuku_point',
      difficultyKey: 'difficulty_basic',
      examples: ['42÷7', '56÷8', '63÷9'],
      settings: [fixedSetting('remainderMode', 'setting_remainder_label', 'setting_option_none')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['div'], remainder_mode: 'none',
        a_min: 1, a_max: 81, b_min: 1, b_max: 9,
      }),
    },
    {
      id: 'g3-div-remainder',
      titleKey: 'menu_g3_div_remainder_title',
      descKey: 'menu_g3_div_remainder_desc',
      pointKey: 'menu_g3_div_remainder_point',
      difficultyKey: 'difficulty_standard',
      examples: ['47÷6', '29÷4', '53÷8'],
      settings: [fixedSetting('remainderMode', 'setting_remainder_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['div'], remainder_mode: 'required',
        a_min: 1, a_max: 99, b_min: 2, b_max: 9,
      }),
    },
  ],
  'four-operations': [
    {
      id: 'g3-addsub-mixed-result-1000',
      titleKey: 'menu_g3_addsub_mixed_result_1000_title',
      descKey: 'menu_g3_addsub_mixed_result_1000_desc',
      pointKey: 'menu_g3_addsub_mixed_result_1000_point',
      difficultyKey: 'difficulty_standard',
      examples: ['620+250+90', '840-320+180', '410+260-150'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_addsub_mixed')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub'], terms: 3, mixed_operators: true,
        a_min: 1, a_max: 999, b_min: 1, b_max: 999, result_max: 1000,
      }),
    },
    {
      id: 'g3-parentheses-mul-result-1000',
      titleKey: 'menu_g3_parentheses_mul_result_1000_title',
      descKey: 'menu_g3_parentheses_mul_result_1000_desc',
      pointKey: 'menu_g3_parentheses_mul_result_1000_point',
      difficultyKey: 'difficulty_standard',
      examples: ['(45+38)×12-56', '(23+17)×8+15', '(90-34)×5-20'],
      settings: [
        fixedSetting('operators', 'setting_operators_label', 'setting_option_addsubmul_mixed'),
        fixedSetting('parentheses', 'setting_parentheses_label', 'setting_option_present'),
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub', 'mul'], terms: 3, mixed_operators: true,
        use_parentheses: true, a_min: 1, a_max: 99, b_min: 1, b_max: 99, result_max: 1000,
      }),
    },
  ],
};

// ---------------------------------------------------------------------
// Grade 4
// ---------------------------------------------------------------------

const NUMBER_KIND_OPTIONS = [
  { value: 'fraction', labelKey: 'setting_option_fraction_only' },
  { value: 'mixedNumber', labelKey: 'setting_option_fraction_with_mixed' },
  { value: 'mixed', labelKey: 'setting_option_mixed', hintKey: 'setting_mixed_hint' },
];

// Maps the 数の種類(分数/帯分数を含む/まぜる) numberKind setting to
// nuts_calc_tex.py's frac --a-fraction-form/--b-fraction-form (#112).
// 'fraction' omits both flags so the request keeps the CLI's 'proper'
// default (unreduced non-mixed operands, unchanged from before #112).
function fractionFormParams(state) {
  const numberKind = state?.numberKind ?? 'mixed';
  if (numberKind === 'fraction') return {};
  const form = numberKind === 'mixedNumber' ? 'mixed' : 'mix';
  return { a_fraction_form: form, b_fraction_form: form };
}

const grade4 = {
  division: [
    {
      id: 'g4-div-1digit',
      titleKey: 'menu_g4_div_1digit_title',
      descKey: 'menu_g4_div_1digit_desc',
      pointKey: 'menu_g4_div_1digit_point',
      difficultyKey: 'difficulty_basic',
      examples: ['84÷4', '864÷6', '392÷7'],
      examplesFor: examplesByChoice(['remainderMode'], {
        none: ['84÷4', '864÷6', '392÷7'],
        required: ['85÷4', '865÷6', '393÷7'],
        mixed: ['84÷4', '864÷6', '392÷7'],
      }),
      settings: [remainderSetting('setting_remainder_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['div'], remainder_mode: remainderModeParam(state),
        a_min: 10, a_max: 999, b_min: 2, b_max: 9,
      }),
    },
    {
      id: 'g4-div-2digit',
      titleKey: 'menu_g4_div_2digit_title',
      descKey: 'menu_g4_div_2digit_desc',
      pointKey: 'menu_g4_div_2digit_point',
      difficultyKey: 'difficulty_standard',
      examples: ['96÷12', '936÷24', '450÷15'],
      examplesFor: examplesByChoice(['remainderMode'], {
        none: ['96÷12', '936÷24', '450÷15'],
        required: ['97÷12', '937÷24', '451÷15'],
        mixed: ['96÷12', '936÷24', '450÷15'],
      }),
      settings: [remainderSetting('setting_remainder_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['div'], remainder_mode: remainderModeParam(state),
        a_min: 100, a_max: 999, b_min: 10, b_max: 99,
      }),
    },
    {
      id: 'g4-decimal-div-int',
      titleKey: 'menu_g4_decimal_div_int_title',
      descKey: 'menu_g4_decimal_div_int_desc',
      pointKey: 'menu_g4_decimal_div_int_point',
      difficultyKey: 'difficulty_standard',
      examples: ['8.4÷4', '7.35÷5', '9.6÷8'],
      settings: [fixedSetting('divisor', 'setting_divisor_label', 'setting_option_integer')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['div'], a_value: 2, b_value: 1, a_decimal_places: 1,
      }),
    },
  ],
  addition: [
    {
      id: 'g4-decimal-add',
      titleKey: 'menu_g4_decimal_add_title',
      descKey: 'menu_g4_decimal_add_desc',
      pointKey: 'menu_g4_decimal_add_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3.74+2.8', '4.36+1.57', '5.67+2.89'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['1.23+2.45', '5.12+3.14', '3.21+4.56'],
        required: ['3.74+2.8', '4.36+1.57', '5.67+2.89'],
        mixed: ['3.74+2.8', '4.36+1.57', '5.67+2.89'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], a_value: 3, b_value: 3,
        a_decimal_places: 2, b_decimal_places: 2, ...carryModeField(['add'], state),
      }),
    },
  ],
  subtraction: [
    {
      id: 'g4-decimal-sub',
      titleKey: 'menu_g4_decimal_sub_title',
      descKey: 'menu_g4_decimal_sub_desc',
      pointKey: 'menu_g4_decimal_sub_point',
      difficultyKey: 'difficulty_basic',
      examples: ['8.2-3.47', '6.35-2.8', '7.15-2.68'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['9.87-3.21', '8.65-1.23', '7.64-2.31'],
        required: ['8.2-3.47', '6.35-2.8', '7.15-2.68'],
        mixed: ['8.2-3.47', '6.35-2.8', '7.15-2.68'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], a_value: 3, b_value: 3,
        a_decimal_places: 2, b_decimal_places: 2, ...carryModeField(['sub'], state),
      }),
    },
  ],
  multiplication: [
    {
      id: 'g4-decimal-mul-int',
      titleKey: 'menu_g4_decimal_mul_int_title',
      descKey: 'menu_g4_decimal_mul_int_desc',
      pointKey: 'menu_g4_decimal_mul_int_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3.6×7', '2.35×4', '5.8×3'],
      settings: [fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_integer')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1, a_decimal_places: 1,
      }),
    },
  ],
  fraction: [
    {
      id: 'g4-fraction-add',
      titleKey: 'menu_g4_fraction_add_title',
      descKey: 'menu_g4_fraction_add_desc',
      pointKey: 'menu_g4_fraction_add_point',
      difficultyKey: 'difficulty_basic_standard',
      examples: ['3/8+2/8', '1 2/5+2 4/5', '2/9+5/9'],
      examplesFor: examplesByChoice(['numberKind'], {
        fraction: ['3/8+2/8', '2/9+5/9', '4/7+2/7'],
        mixedNumber: ['1 2/5+2 4/5', '2 1/6+1 3/6', '3 2/7+1 4/7'],
        mixed: ['3/8+2/8', '1 2/5+2 4/5', '2/9+5/9'],
      }),
      settings: [
        fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator'),
        { id: 'numberKind', labelKey: 'setting_number_kind_label', type: 'choice', options: NUMBER_KIND_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'frac', operator: ['add'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, ...fractionFormParams(state),
      }),
    },
    {
      id: 'g4-fraction-sub',
      titleKey: 'menu_g4_fraction_sub_title',
      descKey: 'menu_g4_fraction_sub_desc',
      pointKey: 'menu_g4_fraction_sub_point',
      difficultyKey: 'difficulty_basic_standard',
      examples: ['7/9-4/9', '3 2/5-1 4/5', '6/8-3/8'],
      examplesFor: examplesByChoice(['numberKind'], {
        fraction: ['7/9-4/9', '6/8-3/8', '5/7-2/7'],
        mixedNumber: ['3 2/5-1 4/5', '4 1/6-2 3/6', '2 3/8-1 5/8'],
        mixed: ['7/9-4/9', '3 2/5-1 4/5', '6/8-3/8'],
      }),
      settings: [
        fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator'),
        { id: 'numberKind', labelKey: 'setting_number_kind_label', type: 'choice', options: NUMBER_KIND_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      // proper_result (答え<1) only makes sense for the plain-fraction tier:
      // 帯分数を含む/まぜる's example (3 2/5-1 4/5=1 3/5, #112) can legitimately
      // answer >= 1 via whole-number borrowing.
      buildParams: (state) => ({
        command_type: 'frac', operator: ['sub'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, proper_result: (state?.numberKind ?? 'mixed') === 'fraction',
        ...fractionFormParams(state),
      }),
    },
  ],
  'four-operations': [
    {
      id: 'g4-four-operations',
      titleKey: 'menu_g4_four_operations_title',
      descKey: 'menu_g4_four_operations_desc',
      pointKey: 'menu_g4_four_operations_point',
      difficultyKey: 'difficulty_standard',
      examples: ['8+12÷3×2', '6×4-9÷3', '15-8÷2+4'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_four_operations')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub', 'mul', 'div'], mixed_operators: true, terms: 3,
        a_value: 1, b_value: 1,
      }),
    },
    {
      id: 'g4-parentheses',
      titleKey: 'menu_g4_parentheses_title',
      descKey: 'menu_g4_parentheses_desc',
      pointKey: 'menu_g4_parentheses_point',
      difficultyKey: 'difficulty_standard',
      examples: ['(8+4)×5-6', '(9-3)×4+7', '(6+5)×3-8'],
      settings: [fixedSetting('parentheses', 'setting_parentheses_label', 'setting_option_present')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add', 'sub', 'mul', 'div'], mixed_operators: true,
        use_parentheses: true, a_value: 1, b_value: 1,
      }),
    },
  ],
};

const DENOMINATOR_CHOICE_OPTIONS = [
  { value: 'same', labelKey: 'setting_option_same_denominator' },
  { value: 'different', labelKey: 'setting_option_different_denominator' },
  { value: 'mixed', labelKey: 'setting_option_mixed', hintKey: 'setting_mixed_hint' },
];

function denominatorParams(state) {
  const denominator = state?.denominator ?? 'mixed';
  if (denominator === 'same') return { same_denominator: true };
  if (denominator === 'different') return { different_denominators: true };
  return {};
}

const REDUCTION_OPTIONS = [OPT_NONE, OPT_REQUIRED, OPT_MIXED];

// ---------------------------------------------------------------------
// Grade 5
// ---------------------------------------------------------------------

const grade5 = {
  multiplication: [
    {
      id: 'g5-decimal-mul',
      titleKey: 'menu_g5_decimal_mul_title',
      descKey: 'menu_g5_decimal_mul_desc',
      pointKey: 'menu_g5_decimal_mul_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3.6×2.4', '0.25×1.6', '4.2×1.5'],
      settings: [fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_decimal')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 2,
        a_decimal_places: 1, b_decimal_places: 1,
      }),
    },
  ],
  division: [
    {
      id: 'g5-decimal-div',
      titleKey: 'menu_g5_decimal_div_title',
      descKey: 'menu_g5_decimal_div_desc',
      pointKey: 'menu_g5_decimal_div_point',
      difficultyKey: 'difficulty_standard',
      examples: ['7.56÷1.2', '4.8÷0.6', '9.36÷2.4'],
      settings: [fixedSetting('divisor', 'setting_divisor_label', 'setting_option_decimal')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['div'], a_value: 2, b_value: 2,
        a_decimal_places: 1, b_decimal_places: 1,
      }),
    },
  ],
  'four-operations': [
    {
      id: 'g5-decimal-four-ops',
      titleKey: 'menu_g5_decimal_four_ops_title',
      descKey: 'menu_g5_decimal_four_ops_desc',
      pointKey: 'menu_g5_decimal_four_ops_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3.6×2.5+4.8÷1.2', '5.4-2.1×1.5', '7.2÷0.9+3.6'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_four_operations')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['add', 'sub', 'mul', 'div'], mixed_operators: true, terms: 3,
        a_kind: ['decimal'], b_kind: ['decimal'], decimal_places: 1,
      }),
    },
  ],
  fraction: [
    {
      id: 'g5-simplify',
      titleKey: 'menu_g5_simplify_title',
      descKey: 'menu_g5_simplify_desc',
      pointKey: 'menu_g5_simplify_point',
      difficultyKey: 'difficulty_basic',
      examples: ['18/24 → 3/4', '16/20 → 4/5', '21/28 → 3/4'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'simplify', numerator_digits: 2, denominator_digits: 2 }),
    },
    {
      id: 'g5-commondenom',
      titleKey: 'menu_g5_commondenom_title',
      descKey: 'menu_g5_commondenom_desc',
      pointKey: 'menu_g5_commondenom_point',
      difficultyKey: 'difficulty_basic',
      examples: ['1/3, 1/4 → 4/12, 3/12', '1/2, 1/5 → 5/10, 2/10', '2/3, 1/6 → 4/6, 1/6'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'commondenom', numerator_digits: 1, denominator_digits: 1 }),
    },
    {
      id: 'g5-fraction-add',
      titleKey: 'menu_g5_fraction_add_title',
      descKey: 'menu_g5_fraction_add_desc',
      pointKey: 'menu_g5_fraction_add_point',
      difficultyKey: 'difficulty_standard',
      examples: ['2/3+3/5', '1 2/3+2 3/5', '2/5+1/5'],
      examplesFor: examplesByChoice(['denominator', 'numberKind'], {
        same_fraction: ['2/5+1/5', '3/7+2/7', '1/6+4/6'],
        same_mixedNumber: ['1 2/5+2 1/5', '2 3/7+1 2/7', '3 1/6+1 4/6'],
        same_mixed: ['2/5+1/5', '1 2/5+2 1/5', '3/7+2/7'],
        different_fraction: ['2/3+3/5', '1/4+2/3', '3/8+1/5'],
        different_mixedNumber: ['1 2/3+2 3/5', '2 1/4+1 2/3', '1 3/8+2 1/5'],
        different_mixed: ['2/3+3/5', '1 2/3+2 3/5', '1/4+2/3'],
        mixed_fraction: ['2/5+1/5', '2/3+3/5', '3/7+2/7'],
        mixed_mixedNumber: ['1 2/5+2 1/5', '1 2/3+2 3/5', '2 3/7+1 2/7'],
        mixed_mixed: ['2/3+3/5', '1 2/3+2 3/5', '2/5+1/5'],
      }),
      settings: [
        { id: 'denominator', labelKey: 'setting_denominator_label', type: 'choice', options: DENOMINATOR_CHOICE_OPTIONS, default: 'mixed' },
        { id: 'numberKind', labelKey: 'setting_number_kind_label', type: 'choice', options: NUMBER_KIND_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'frac', operator: ['add'], numerator_digits: 1, denominator_digits: 1,
        ...denominatorParams(state), ...fractionFormParams(state),
      }),
    },
    {
      id: 'g5-fraction-sub',
      titleKey: 'menu_g5_fraction_sub_title',
      descKey: 'menu_g5_fraction_sub_desc',
      pointKey: 'menu_g5_fraction_sub_point',
      difficultyKey: 'difficulty_standard',
      examples: ['5/6-1/4', '3 5/6-1 1/4', '4/7-1/7'],
      examplesFor: examplesByChoice(['denominator', 'numberKind'], {
        same_fraction: ['4/7-1/7', '5/9-2/9', '3/8-1/8'],
        same_mixedNumber: ['2 4/7-1 1/7', '3 5/9-1 2/9', '4 3/8-2 1/8'],
        same_mixed: ['4/7-1/7', '2 4/7-1 1/7', '5/9-2/9'],
        different_fraction: ['5/6-1/4', '3/4-1/3', '7/8-2/5'],
        different_mixedNumber: ['3 5/6-1 1/4', '2 3/4-1 1/3', '4 7/8-2 2/5'],
        different_mixed: ['5/6-1/4', '3 5/6-1 1/4', '3/4-1/3'],
        mixed_fraction: ['4/7-1/7', '5/6-1/4', '5/9-2/9'],
        mixed_mixedNumber: ['2 4/7-1 1/7', '3 5/6-1 1/4', '3 5/9-1 2/9'],
        mixed_mixed: ['5/6-1/4', '3 5/6-1 1/4', '4/7-1/7'],
      }),
      settings: [
        { id: 'denominator', labelKey: 'setting_denominator_label', type: 'choice', options: DENOMINATOR_CHOICE_OPTIONS, default: 'mixed' },
        { id: 'numberKind', labelKey: 'setting_number_kind_label', type: 'choice', options: NUMBER_KIND_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      // proper_result only for the plain-fraction tier -- see g4-fraction-sub note (#112).
      buildParams: (state) => ({
        command_type: 'frac', operator: ['sub'], numerator_digits: 1, denominator_digits: 1,
        proper_result: (state?.numberKind ?? 'mixed') === 'fraction',
        ...denominatorParams(state), ...fractionFormParams(state),
      }),
    },
    {
      id: 'g5-frac2dec',
      titleKey: 'menu_g5_frac2dec_title',
      descKey: 'menu_g5_frac2dec_desc',
      pointKey: 'menu_g5_frac2dec_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3/4 → 0.75', '1/8 → 0.125', '7/20 → 0.35'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'frac2dec', numerator_digits: 1, denominator_digits: 1 }),
    },
    {
      id: 'g5-dec2frac',
      titleKey: 'menu_g5_dec2frac_title',
      descKey: 'menu_g5_dec2frac_desc',
      pointKey: 'menu_g5_dec2frac_point',
      difficultyKey: 'difficulty_basic',
      examples: ['0.6 → 3/5', '0.25 → 1/4', '0.75 → 3/4'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'dec2frac' }),
    },
    {
      id: 'g5-divfrac',
      titleKey: 'menu_g5_divfrac_title',
      descKey: 'menu_g5_divfrac_desc',
      pointKey: 'menu_g5_divfrac_point',
      difficultyKey: 'difficulty_basic',
      examples: ['2÷3 → 2/3', '4÷5 → 4/5', '3÷7 → 3/7'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'divfrac', a_min: 1, a_max: 9, b_min: 2, b_max: 9 }),
    },
  ],
  'number-sense': [
    {
      id: 'g5-evenodd',
      titleKey: 'menu_g5_evenodd_title',
      descKey: 'menu_g5_evenodd_desc',
      pointKey: 'menu_g5_evenodd_point',
      difficultyKey: 'difficulty_basic',
      examples: ['37 → 奇数', '48 → 偶数', '63 → 奇数'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'evenodd', a_min: 1, a_max: 100 }),
    },
    {
      id: 'g5-multiples',
      titleKey: 'menu_g5_multiples_title',
      descKey: 'menu_g5_multiples_desc',
      pointKey: 'menu_g5_multiples_point',
      difficultyKey: 'difficulty_basic',
      examples: ['6 → 6,12,18,…', '4 → 4,8,12,…', '9 → 9,18,27,…'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'multiples', a_min: 2, a_max: 12 }),
    },
    {
      id: 'g5-divisors',
      titleKey: 'menu_g5_divisors_title',
      descKey: 'menu_g5_divisors_desc',
      pointKey: 'menu_g5_divisors_point',
      difficultyKey: 'difficulty_basic',
      examples: ['12 → 1,2,3,4,6,12', '18 → 1,2,3,6,9,18', '24 → 1,2,3,4,6,8,12,24'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'divisors', a_min: 6, a_max: 60 }),
    },
    {
      id: 'g5-lcm',
      titleKey: 'menu_g5_lcm_title',
      descKey: 'menu_g5_lcm_desc',
      pointKey: 'menu_g5_lcm_point',
      difficultyKey: 'difficulty_standard',
      examples: ['6と8 → 最小公倍数24', '4と6 → 最小公倍数12', '9と12 → 最小公倍数36'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'lcm', a_min: 4, a_max: 40, b_min: 4, b_max: 40 }),
    },
    {
      id: 'g5-gcd',
      titleKey: 'menu_g5_gcd_title',
      descKey: 'menu_g5_gcd_desc',
      pointKey: 'menu_g5_gcd_point',
      difficultyKey: 'difficulty_standard',
      examples: ['18と24 → 最大公約数6', '12と16 → 最大公約数4', '20と30 → 最大公約数10'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'gcd', a_min: 4, a_max: 40, b_min: 4, b_max: 40 }),
    },
  ],
};

// ---------------------------------------------------------------------
// Grade 6
// ---------------------------------------------------------------------

const grade6 = {
  fraction: [
    {
      id: 'g6-fraction-mul-int',
      titleKey: 'menu_g6_fraction_mul_int_title',
      descKey: 'menu_g6_fraction_mul_int_desc',
      pointKey: 'menu_g6_fraction_mul_int_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3/5×4', '4/6×3', '2/7×5'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['3/5×4', '2/7×5', '3/8×3'],
        required: ['4/6×3', '2/4×3', '6/8×2'],
        mixed: ['3/5×4', '4/6×3', '2/7×5'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_integer'),
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'mixed', operator: ['mul'], a_kind: ['fraction'], b_kind: ['int'],
        numerator_digits: 1, denominator_digits: 1, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-int-mul-fraction',
      titleKey: 'menu_g6_int_mul_fraction_title',
      descKey: 'menu_g6_int_mul_fraction_desc',
      pointKey: 'menu_g6_int_mul_fraction_point',
      difficultyKey: 'difficulty_basic',
      examples: ['4×3/5', '3×4/6', '5×2/7'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['4×3/5', '5×2/7', '3×3/8'],
        required: ['3×4/6', '3×2/4', '2×6/8'],
        mixed: ['4×3/5', '3×4/6', '5×2/7'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('multiplicand', 'setting_multiplicand_label', 'setting_option_integer'),
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'mixed', operator: ['mul'], a_kind: ['int'], b_kind: ['fraction'],
        numerator_digits: 1, denominator_digits: 1, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-fraction-mul',
      titleKey: 'menu_g6_fraction_mul_title',
      descKey: 'menu_g6_fraction_mul_desc',
      pointKey: 'menu_g6_fraction_mul_point',
      difficultyKey: 'difficulty_basic',
      examples: ['3/5×7/9', '2/5×3/7', '3/8×2/9'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['2/5×3/7', '3/8×2/9', '4/7×1/6'],
        required: ['3/5×7/9', '2/4×3/6', '4/6×2/8'],
        mixed: ['3/5×7/9', '2/5×3/7', '3/8×2/9'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'frac', operator: ['mul'], numerator_digits: 1, denominator_digits: 1,
        proper_operands: true, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-fraction-div-int',
      titleKey: 'menu_g6_fraction_div_int_title',
      descKey: 'menu_g6_fraction_div_int_desc',
      pointKey: 'menu_g6_fraction_div_int_point',
      difficultyKey: 'difficulty_basic',
      examples: ['5/6÷3', '4/6÷2', '3/7÷2'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['5/6÷3', '3/7÷2', '4/9÷5'],
        required: ['4/6÷2', '6/8÷3', '2/4÷2'],
        mixed: ['5/6÷3', '4/6÷2', '3/7÷2'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('divisor', 'setting_divisor_label', 'setting_option_integer'),
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'mixed', operator: ['div'], a_kind: ['fraction'], b_kind: ['int'],
        numerator_digits: 1, denominator_digits: 1, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-int-div-fraction',
      titleKey: 'menu_g6_int_div_fraction_title',
      descKey: 'menu_g6_int_div_fraction_desc',
      pointKey: 'menu_g6_int_div_fraction_point',
      difficultyKey: 'difficulty_standard',
      examples: ['4÷2/3', '4÷3/5', '5÷2/7'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['4÷3/5', '5÷2/7', '3÷4/9'],
        required: ['4÷2/3', '3÷2/4', '2÷4/8'],
        mixed: ['4÷2/3', '4÷3/5', '5÷2/7'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('divisor', 'setting_divisor_label', 'setting_option_fraction'),
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'mixed', operator: ['div'], a_kind: ['int'], b_kind: ['fraction'],
        numerator_digits: 1, denominator_digits: 1, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-fraction-div',
      titleKey: 'menu_g6_fraction_div_title',
      descKey: 'menu_g6_fraction_div_desc',
      pointKey: 'menu_g6_fraction_div_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3/4÷2/5', '2/4÷2/6', '2/7÷3/8'],
      examplesFor: examplesByChoice(['reduction'], {
        none: ['3/4÷2/5', '2/7÷3/8', '4/9÷1/6'],
        required: ['2/4÷2/6', '3/6÷2/8', '4/8÷2/4'],
        mixed: ['3/4÷2/5', '2/4÷2/6', '2/7÷3/8'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'frac', operator: ['div'], numerator_digits: 1, denominator_digits: 1,
        proper_operands: true, reducible_mode: reducibleModeParam(state),
      }),
    },
    {
      id: 'g6-fraction-muldiv-mixed',
      titleKey: 'menu_g6_fraction_muldiv_mixed_title',
      descKey: 'menu_g6_fraction_muldiv_mixed_desc',
      pointKey: 'menu_g6_fraction_muldiv_mixed_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3/4×2/5÷7/10', '2/3÷1/4×3/5', '5/6×2/7÷3/8'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_muldiv_mixed')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['mul', 'div'], mixed_operators: true, terms: 3,
        a_kind: ['fraction'], b_kind: ['fraction'], numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-fraction-four-ops',
      titleKey: 'menu_g6_fraction_four_ops_title',
      descKey: 'menu_g6_fraction_four_ops_desc',
      pointKey: 'menu_g6_fraction_four_ops_point',
      difficultyKey: 'difficulty_standard',
      examples: ['2/3+1/4×6/5', '3/4-2/5÷1/3', '5/6×2/3-1/4'],
      settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_four_operations')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['add', 'sub', 'mul', 'div'], mixed_operators: true, terms: 3,
        a_kind: ['fraction'], b_kind: ['fraction'], numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-fraction-decimal-mixed',
      titleKey: 'menu_g6_fraction_decimal_mixed_title',
      descKey: 'menu_g6_fraction_decimal_mixed_desc',
      pointKey: 'menu_g6_fraction_decimal_mixed_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3/4+0.5', '0.25+1/8', '2/5+0.6'],
      settings: [fixedSetting('numberKind', 'setting_number_kind_label', 'setting_option_fraction_decimal_mixed')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['add'], a_kind: ['fraction', 'decimal'], b_kind: ['fraction', 'decimal'],
        numerator_digits: 1, denominator_digits: 1, decimal_places: 1,
      }),
    },
  ],
};

// ---------------------------------------------------------------------
// Ungraded
// ---------------------------------------------------------------------
//
// aBc (mental-math decomposition) and squ (same-number multiplication) are
// generic drills with no course-of-study grade anchor and no entry in
// docs/uiux/calculation_drill_menu_parameters_v1.md; kept as-is (out of
// this doc-parity rebuild's scope, per issue #98 discussion).

const ungraded = {
  'number-sense': [
    {
      id: 'ungraded-abc',
      titleKey: 'menu_ungraded_abc_title',
      descKey: 'menu_ungraded_abc_desc',
      pointKey: 'menu_ungraded_abc_point',
      difficultyKey: 'difficulty_standard',
      examples: ['3214 → 334', '5827 → 607', '1096 → 196'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'aBc' }),
    },
    {
      id: 'ungraded-squ',
      titleKey: 'menu_ungraded_squ_title',
      descKey: 'menu_ungraded_squ_desc',
      pointKey: 'menu_ungraded_squ_point',
      difficultyKey: 'difficulty_basic',
      examples: ['1×1', '2×2', '3×3'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'squ', a_value: 1 }),
    },
  ],
};

export const presetsByGrade = {
  1: grade1,
  2: grade2,
  3: grade3,
  4: grade4,
  5: grade5,
  6: grade6,
  [UNGRADED]: ungraded,
};
