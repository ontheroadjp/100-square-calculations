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
// mixing gate semantics per item would complicate drillCatalog.js for no
// practical benefit (frontend/web only ever runs against one active
// renderer at a time, selected server-side via NUTS_CALC_RENDERER).

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
      difficultyKey: 'difficulty_basic',
      examples: ['3+5', '6+4'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], carry_mode: 'none',
        a_min: 1, a_max: 9, b_min: 1, b_max: 9,
      }),
    },
    {
      id: 'g1-add-20',
      titleKey: 'menu_g1_add_20_title',
      descKey: 'menu_g1_add_20_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['8+7', '9+6'],
      settings: [fixedSetting('carryMode', 'setting_carry_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], carry_mode: 'required',
        a_min: 1, a_max: 9, b_min: 1, b_max: 9,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g1-sub-10',
      titleKey: 'menu_g1_sub_10_title',
      descKey: 'menu_g1_sub_10_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['8-3', '10-6'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'],
        a_min: 2, a_max: 10, b_min: 1, b_max: 9,
      }),
    },
    {
      id: 'g1-sub-20',
      titleKey: 'menu_g1_sub_20_title',
      descKey: 'menu_g1_sub_20_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['13-7', '16-9'],
      settings: [fixedSetting('carryMode', 'setting_borrow_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'], carry_mode: 'required',
        a_min: 10, a_max: 19, b_min: 1, b_max: 9,
      }),
    },
  ],
  'four-operations': [
    {
      id: 'g1-three-terms',
      titleKey: 'menu_g1_three_terms_title',
      descKey: 'menu_g1_three_terms_desc',
      difficultyKey: 'difficulty_advanced',
      examples: ['3+4+2', '8-3+4'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['34+5', '7+26', '42+35'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['34+5', '42+35'],
        required: ['7+26', '48+37'],
        mixed: ['34+5', '7+26', '42+35'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 99, b_min: 1, b_max: 99,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g2-sub-2digit',
      titleKey: 'menu_g2_sub_2digit_title',
      descKey: 'menu_g2_sub_2digit_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['38-5', '32-7', '72-48'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['38-5', '95-23'],
        required: ['32-7', '72-48'],
        mixed: ['38-5', '32-7', '72-48'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 10, a_max: 99, b_min: 1, b_max: 99,
      }),
    },
  ],
  multiplication: [
    {
      id: 'g2-kuku',
      titleKey: 'menu_g2_kuku_title',
      descKey: 'menu_g2_kuku_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['3×7', '8×6'],
      examplesFor: (state) => {
        const dan = state?.dan ?? 'mixed';
        if (dan === 'mixed') return ['3×7', '8×6'];
        const examplesByOrder = {
          ascending: [`${dan}×1`, `${dan}×2`],
          descending: [`${dan}×9`, `${dan}×8`],
          random: [`${dan}×6`, `${dan}×3`],
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
      difficultyKey: 'difficulty_standard',
      examples: ['35+24-18'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['35-(12+8)'],
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
      id: 'g3-add-3digit',
      titleKey: 'menu_g3_add_3digit_title',
      descKey: 'menu_g3_add_3digit_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['625+75', '263+1', '521+365'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['263+1', '521+365'],
        required: ['625+75', '486+275'],
        mixed: ['625+75', '263+1', '521+365'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 999, b_min: 1, b_max: 999,
      }),
    },
    {
      id: 'g3-add-4digit',
      titleKey: 'menu_g3_add_4digit_title',
      descKey: 'menu_g3_add_4digit_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['3258+46', '583+2417'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['1234+5', '6123+1642'],
        required: ['3258+46', '583+2417'],
        mixed: ['3258+46', '583+2417'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['add'], ...carryModeField(['add'], state),
        a_min: 1, a_max: 9999, b_min: 1, b_max: 9999,
      }),
    },
    {
      id: 'g3-decimal-addsub',
      titleKey: 'menu_g3_decimal_addsub_title',
      descKey: 'menu_g3_decimal_addsub_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['2.4+3.1', '4.7+1.6'],
      // Partial: nuts_calc_tex.py's --carry-borrow family rejects
      // --a-decimal-places/--b-decimal-places (nuts_calc_tex.py:610-611),
      // so the carry setting can't be honored yet. Tracked in #113. The
      // preview below is illustrative only (matches the setting's meaning,
      // not what the backend will actually generate).
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['2.4+3.1'],
        required: ['4.7+1.6'],
        mixed: ['2.4+3.1', '4.7+1.6'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], a_value: 1, b_value: 1,
        a_decimal_places: 1, b_decimal_places: 1,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g3-sub-3digit',
      titleKey: 'menu_g3_sub_3digit_title',
      descKey: 'menu_g3_sub_3digit_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['625-75', '521-365'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['586-123', '768-345'],
        required: ['625-75', '521-365'],
        mixed: ['625-75', '521-365'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 100, a_max: 999, b_min: 1, b_max: 999,
      }),
    },
    {
      id: 'g3-sub-4digit',
      titleKey: 'menu_g3_sub_4digit_title',
      descKey: 'menu_g3_sub_4digit_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['3258-46', '7234-3587'],
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['3258-46', '9876-1234'],
        required: ['7234-3587', '5000-1234'],
        mixed: ['3258-46', '7234-3587'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: (state) => ({
        command_type: 'ope', operator: ['sub'], ...carryModeField(['sub'], state),
        a_min: 1000, a_max: 9999, b_min: 1, b_max: 9999,
      }),
    },
    {
      id: 'g3-decimal-sub',
      titleKey: 'menu_g3_decimal_sub_title',
      descKey: 'menu_g3_decimal_sub_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['5.7-2.3', '8.4-3.9'],
      // Partial: see g3-decimal-addsub above (#113). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['5.7-2.3'],
        required: ['8.4-3.9'],
        mixed: ['5.7-2.3', '8.4-3.9'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'], a_value: 1, b_value: 1,
        a_decimal_places: 1, b_decimal_places: 1,
      }),
    },
  ],
  multiplication: [
    {
      id: 'g3-mul-2x1',
      titleKey: 'menu_g3_mul_2x1_title',
      descKey: 'menu_g3_mul_2x1_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['38×7', '24×5'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1 }),
    },
    {
      id: 'g3-mul-3x1',
      titleKey: 'menu_g3_mul_3x1_title',
      descKey: 'menu_g3_mul_3x1_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['326×4', '425×7'],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'ope', operator: ['mul'], a_value: 3, b_value: 1 }),
    },
    {
      id: 'g3-mul-2x2',
      titleKey: 'menu_g3_mul_2x2_title',
      descKey: 'menu_g3_mul_2x2_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['47×23', '34×28'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['42÷7', '56÷8'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['47÷6', '29÷4'],
      settings: [fixedSetting('remainderMode', 'setting_remainder_label', 'setting_option_required')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['div'], remainder_mode: 'required',
        a_min: 1, a_max: 99, b_min: 2, b_max: 9,
      }),
    },
  ],
  fraction: [
    {
      id: 'g3-fraction-add',
      titleKey: 'menu_g3_fraction_add_title',
      descKey: 'menu_g3_fraction_add_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['2/7+3/7'],
      settings: [fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['add'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, proper_operands: true, proper_result: true,
      }),
    },
    {
      id: 'g3-fraction-sub',
      titleKey: 'menu_g3_fraction_sub_title',
      descKey: 'menu_g3_fraction_sub_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['6/7-2/7'],
      settings: [fixedSetting('denominator', 'setting_denominator_label', 'setting_option_same_denominator')],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['sub'], numerator_digits: 1, denominator_digits: 1,
        same_denominator: true, proper_operands: true, proper_result: true,
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
      difficultyKey: 'difficulty_basic',
      examples: ['84÷4', '864÷6'],
      examplesFor: examplesByChoice(['remainderMode'], {
        none: ['84÷4', '864÷6'],
        required: ['85÷4', '865÷6'],
        mixed: ['84÷4', '864÷6'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['96÷12', '936÷24'],
      examplesFor: examplesByChoice(['remainderMode'], {
        none: ['96÷12', '936÷24'],
        required: ['97÷12', '937÷24'],
        mixed: ['96÷12', '936÷24'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['8.4÷4', '7.35÷5'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['3.74+2.8', '4.36+1.57'],
      // Partial: see grade3 decimal add/sub (#113); carry setting can't be
      // honored alongside --a-decimal-places/--b-decimal-places yet. The
      // preview below is illustrative only, for the same reason.
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['1.23+2.45', '5.12+3.14'],
        required: ['3.74+2.8', '4.36+1.57'],
        mixed: ['3.74+2.8', '4.36+1.57'],
      }),
      settings: [carrySetting('setting_carry_label')],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['add'], a_value: 3, b_value: 3,
        a_decimal_places: 2, b_decimal_places: 2,
      }),
    },
  ],
  subtraction: [
    {
      id: 'g4-decimal-sub',
      titleKey: 'menu_g4_decimal_sub_title',
      descKey: 'menu_g4_decimal_sub_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['8.2-3.47', '6.35-2.8'],
      // Partial: see g4-decimal-add above (#113). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['carryMode'], {
        none: ['9.87-3.21', '8.65-1.23'],
        required: ['8.2-3.47', '6.35-2.8'],
        mixed: ['8.2-3.47', '6.35-2.8'],
      }),
      settings: [carrySetting('setting_borrow_label')],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'ope', operator: ['sub'], a_value: 3, b_value: 3,
        a_decimal_places: 2, b_decimal_places: 2,
      }),
    },
  ],
  multiplication: [
    {
      id: 'g4-decimal-mul-int',
      titleKey: 'menu_g4_decimal_mul_int_title',
      descKey: 'menu_g4_decimal_mul_int_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['3.6×7', '2.35×4'],
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
      difficultyKey: 'difficulty_basic_standard',
      examples: ['3/8+2/8', '1 2/5+2 4/5'],
      examplesFor: examplesByChoice(['numberKind'], {
        fraction: ['3/8+2/8'],
        mixedNumber: ['1 2/5+2 4/5'],
        mixed: ['3/8+2/8', '1 2/5+2 4/5'],
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
      difficultyKey: 'difficulty_basic_standard',
      examples: ['7/9-4/9', '3 2/5-1 4/5'],
      examplesFor: examplesByChoice(['numberKind'], {
        fraction: ['7/9-4/9'],
        mixedNumber: ['3 2/5-1 4/5'],
        mixed: ['7/9-4/9', '3 2/5-1 4/5'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['8+12÷3×2'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['(8+4)×5-6'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['3.6×2.4', '0.25×1.6'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['7.56÷1.2', '4.8÷0.6'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['3.6×2.5+4.8÷1.2'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['18/24 → 3/4'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'simplify', numerator_digits: 2, denominator_digits: 2 }),
    },
    {
      id: 'g5-commondenom',
      titleKey: 'menu_g5_commondenom_title',
      descKey: 'menu_g5_commondenom_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['1/3, 1/4 → 4/12, 3/12'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'commondenom', numerator_digits: 1, denominator_digits: 1 }),
    },
    {
      id: 'g5-fraction-add',
      titleKey: 'menu_g5_fraction_add_title',
      descKey: 'menu_g5_fraction_add_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['2/3+3/5', '1 2/3+2 3/5'],
      examplesFor: examplesByChoice(['denominator', 'numberKind'], {
        same_fraction: ['2/5+1/5'],
        same_mixedNumber: ['1 2/5+2 1/5'],
        same_mixed: ['2/5+1/5', '1 2/5+2 1/5'],
        different_fraction: ['2/3+3/5'],
        different_mixedNumber: ['1 2/3+2 3/5'],
        different_mixed: ['2/3+3/5', '1 2/3+2 3/5'],
        mixed_fraction: ['2/5+1/5', '2/3+3/5'],
        mixed_mixedNumber: ['1 2/5+2 1/5', '1 2/3+2 3/5'],
        mixed_mixed: ['2/3+3/5', '1 2/3+2 3/5'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['5/6-1/4', '3 5/6-1 1/4'],
      examplesFor: examplesByChoice(['denominator', 'numberKind'], {
        same_fraction: ['4/7-1/7'],
        same_mixedNumber: ['2 4/7-1 1/7'],
        same_mixed: ['4/7-1/7', '2 4/7-1 1/7'],
        different_fraction: ['5/6-1/4'],
        different_mixedNumber: ['3 5/6-1 1/4'],
        different_mixed: ['5/6-1/4', '3 5/6-1 1/4'],
        mixed_fraction: ['4/7-1/7', '5/6-1/4'],
        mixed_mixedNumber: ['2 4/7-1 1/7', '3 5/6-1 1/4'],
        mixed_mixed: ['5/6-1/4', '3 5/6-1 1/4'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['3/4 → 0.75'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'frac2dec', numerator_digits: 1, denominator_digits: 1 }),
    },
    {
      id: 'g5-dec2frac',
      titleKey: 'menu_g5_dec2frac_title',
      descKey: 'menu_g5_dec2frac_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['0.6 → 3/5'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'dec2frac' }),
    },
    {
      id: 'g5-divfrac',
      titleKey: 'menu_g5_divfrac_title',
      descKey: 'menu_g5_divfrac_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['2÷3 → 2/3'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['37 → 奇数', '48 → 偶数'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'evenodd', a_min: 1, a_max: 100 }),
    },
    {
      id: 'g5-multiples',
      titleKey: 'menu_g5_multiples_title',
      descKey: 'menu_g5_multiples_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['6 → 6,12,18,…'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'multiples', a_min: 2, a_max: 12 }),
    },
    {
      id: 'g5-divisors',
      titleKey: 'menu_g5_divisors_title',
      descKey: 'menu_g5_divisors_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['12 → 1,2,3,4,6,12'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'divisors', a_min: 6, a_max: 60 }),
    },
    {
      id: 'g5-lcm',
      titleKey: 'menu_g5_lcm_title',
      descKey: 'menu_g5_lcm_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['6と8 → 最小公倍数24'],
      settings: [],
      supportLevel: 'full',
      latexOnly: true,
      buildParams: () => ({ command_type: 'lcm', a_min: 4, a_max: 40, b_min: 4, b_max: 40 }),
    },
    {
      id: 'g5-gcd',
      titleKey: 'menu_g5_gcd_title',
      descKey: 'menu_g5_gcd_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['18と24 → 最大公約数6'],
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
      difficultyKey: 'difficulty_basic',
      examples: ['3/5×4'],
      // Partial: no way to force/forbid a reducible raw result. #114. The
      // preview below is illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['3/5×4'],
        required: ['4/6×3'],
        mixed: ['3/5×4'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_integer'),
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['mul'], a_kind: ['fraction'], b_kind: ['int'],
        numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-int-mul-fraction',
      titleKey: 'menu_g6_int_mul_fraction_title',
      descKey: 'menu_g6_int_mul_fraction_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['4×3/5'],
      // Partial: see g6-fraction-mul-int above (#114). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['4×3/5'],
        required: ['3×4/6'],
        mixed: ['4×3/5'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('multiplicand', 'setting_multiplicand_label', 'setting_option_integer'),
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['mul'], a_kind: ['int'], b_kind: ['fraction'],
        numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-fraction-mul',
      titleKey: 'menu_g6_fraction_mul_title',
      descKey: 'menu_g6_fraction_mul_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['3/5×7/9'],
      // Partial: see g6-fraction-mul-int above (#114). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['2/5×3/7'],
        required: ['3/5×7/9'],
        mixed: ['3/5×7/9'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['mul'], numerator_digits: 1, denominator_digits: 1,
        proper_operands: true,
      }),
    },
    {
      id: 'g6-fraction-div-int',
      titleKey: 'menu_g6_fraction_div_int_title',
      descKey: 'menu_g6_fraction_div_int_desc',
      difficultyKey: 'difficulty_basic',
      examples: ['5/6÷3'],
      // Partial: see g6-fraction-mul-int above (#114). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['5/6÷3'],
        required: ['4/6÷2'],
        mixed: ['5/6÷3'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('divisor', 'setting_divisor_label', 'setting_option_integer'),
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['div'], a_kind: ['fraction'], b_kind: ['int'],
        numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-int-div-fraction',
      titleKey: 'menu_g6_int_div_fraction_title',
      descKey: 'menu_g6_int_div_fraction_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['4÷2/3'],
      // Partial: see g6-fraction-mul-int above (#114). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['4÷3/5'],
        required: ['4÷2/3'],
        mixed: ['4÷2/3'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
        fixedSetting('divisor', 'setting_divisor_label', 'setting_option_fraction'),
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'mixed', operator: ['div'], a_kind: ['int'], b_kind: ['fraction'],
        numerator_digits: 1, denominator_digits: 1,
      }),
    },
    {
      id: 'g6-fraction-div',
      titleKey: 'menu_g6_fraction_div_title',
      descKey: 'menu_g6_fraction_div_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['3/4÷2/5'],
      // Partial: see g6-fraction-mul-int above (#114). The preview below is
      // illustrative only, for the same reason.
      examplesFor: examplesByChoice(['reduction'], {
        none: ['3/4÷2/5'],
        required: ['2/4÷2/6'],
        mixed: ['3/4÷2/5'],
      }),
      settings: [
        { id: 'reduction', labelKey: 'setting_reduction_label', type: 'choice', options: REDUCTION_OPTIONS, default: 'mixed' },
      ],
      supportLevel: 'partial',
      latexOnly: true,
      buildParams: () => ({
        command_type: 'frac', operator: ['div'], numerator_digits: 1, denominator_digits: 1,
        proper_operands: true,
      }),
    },
    {
      id: 'g6-fraction-muldiv-mixed',
      titleKey: 'menu_g6_fraction_muldiv_mixed_title',
      descKey: 'menu_g6_fraction_muldiv_mixed_desc',
      difficultyKey: 'difficulty_standard',
      examples: ['3/4×2/5÷7/10'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['2/3+1/4×6/5'],
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
      difficultyKey: 'difficulty_standard',
      examples: ['3/4+0.5'],
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
      difficultyKey: 'difficulty_standard',
      examples: [],
      settings: [],
      supportLevel: 'full',
      latexOnly: false,
      buildParams: () => ({ command_type: 'aBc' }),
    },
    {
      id: 'ungraded-squ',
      titleKey: 'menu_ungraded_squ_title',
      descKey: 'menu_ungraded_squ_desc',
      difficultyKey: 'difficulty_basic',
      examples: [],
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
