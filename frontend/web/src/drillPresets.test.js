import { test } from 'node:test';
import assert from 'node:assert/strict';
import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';

const KNOWN_CATEGORIES = new Set([
  'addition', 'subtraction', 'multiplication', 'division',
  'fraction', 'four-operations', 'number-sense',
]);

const KNOWN_SUPPORT_LEVELS = new Set(['full', 'partial', 'none']);
const KNOWN_DIFFICULTY_KEYS = new Set([
  'difficulty_basic',
  'difficulty_standard',
  'difficulty_basic_standard',
  'difficulty_advanced',
]);

function defaultSettingsState(settings) {
  const state = {};
  for (const setting of settings) {
    if (setting.type === 'choice') state[setting.id] = setting.default;
  }
  return state;
}

function allItems() {
  const items = [];
  for (const gradeKey of [...GRADES, UNGRADED]) {
    const categories = presetsByGrade[gradeKey];
    for (const [category, categoryItems] of Object.entries(categories)) {
      for (const item of categoryItems) items.push({ gradeKey, category, item });
    }
  }
  return items;
}

test('every grade (and UNGRADED) has a category map in presetsByGrade', () => {
  for (const gradeKey of [...GRADES, UNGRADED]) {
    assert.ok(presetsByGrade[gradeKey], `missing presetsByGrade[${gradeKey}]`);
    assert.equal(typeof presetsByGrade[gradeKey], 'object');
  }
});

test('every category key is one of the known category ids', () => {
  for (const { gradeKey, category } of allItems()) {
    assert.ok(KNOWN_CATEGORIES.has(category), `grade ${gradeKey} has unknown category "${category}"`);
  }
});

test('every menu item has the required shape', () => {
  for (const { gradeKey, category, item } of allItems()) {
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    assert.equal(typeof item.id, 'string', `${context}: id must be a string`);
    assert.equal(typeof item.titleKey, 'string', `${context}: titleKey must be a string`);
    assert.equal(typeof item.descKey, 'string', `${context}: descKey must be a string`);
    assert.equal(typeof item.pointKey, 'string', `${context}: pointKey must be a string`);
    assert.ok(KNOWN_DIFFICULTY_KEYS.has(item.difficultyKey), `${context}: unknown difficultyKey "${item.difficultyKey}"`);
    assert.ok(Array.isArray(item.examples), `${context}: examples must be an array`);
    assert.ok(Array.isArray(item.settings), `${context}: settings must be an array`);
    assert.equal(typeof item.buildParams, 'function', `${context}: buildParams must be a function`);
    assert.equal(typeof item.latexOnly, 'boolean', `${context}: latexOnly must be a boolean`);
    assert.ok(KNOWN_SUPPORT_LEVELS.has(item.supportLevel), `${context}: unknown supportLevel "${item.supportLevel}"`);
  }
});

test('every settings entry is a valid choice or fixed setting', () => {
  for (const { gradeKey, category, item } of allItems()) {
    for (const setting of item.settings) {
      const context = `grade ${gradeKey} / ${category} / ${item.id} / setting ${setting.id}`;
      assert.equal(typeof setting.id, 'string', `${context}: id must be a string`);
      assert.equal(typeof setting.labelKey, 'string', `${context}: labelKey must be a string`);
      if (setting.type === 'choice') {
        assert.ok(Array.isArray(setting.options) && setting.options.length > 0, `${context}: choice must have options`);
        for (const option of setting.options) {
          assert.equal(typeof option.value, 'string', `${context}: option value must be a string`);
          assert.equal(typeof option.labelKey, 'string', `${context}: option labelKey must be a string`);
        }
        assert.ok(
          setting.options.some((option) => option.value === setting.default),
          `${context}: default "${setting.default}" must match one of the options`,
        );
        if (setting.disabledWhen) assert.equal(typeof setting.disabledWhen, 'function', `${context}: disabledWhen must be a function`);
        if (setting.resolveValue) assert.equal(typeof setting.resolveValue, 'function', `${context}: resolveValue must be a function`);
      } else if (setting.type === 'fixed') {
        assert.equal(typeof setting.valueLabelKey, 'string', `${context}: fixed setting must have valueLabelKey`);
        if (setting.options !== undefined) {
          assert.ok(Array.isArray(setting.options) && setting.options.length > 0, `${context}: fixed options must be a non-empty array when present`);
          for (const option of setting.options) {
            assert.equal(typeof option.value, 'string', `${context}: option value must be a string`);
            assert.equal(typeof option.labelKey, 'string', `${context}: option labelKey must be a string`);
          }
          assert.ok(
            setting.options.some((option) => option.labelKey === setting.valueLabelKey),
            `${context}: valueLabelKey "${setting.valueLabelKey}" must match one of the sibling options`,
          );
        }
      } else {
        assert.fail(`${context}: unknown setting type "${setting.type}"`);
      }
    }
  }
});

test('grade 2 kuku maps each fixed-row question order to renderer parameters', () => {
  const item = presetsByGrade[2].multiplication.find((candidate) => candidate.id === 'g2-kuku');

  assert.deepEqual(item.buildParams({ dan: '1', questionOrder: 'ascending' }), { command_type: '99', a_value: 1 });
  assert.deepEqual(item.buildParams({ dan: '1', questionOrder: 'descending' }), { command_type: '99', a_value: 1, descend: true });
  assert.deepEqual(item.buildParams({ dan: '1', questionOrder: 'random' }), { command_type: '99', a_value: 1, shuffle: true });
});

test('grade 1 and grade 2 basic drills declare a self-documenting result_max even where already structurally bounded (issue #176)', () => {
  const grade1 = presetsByGrade[1];
  const grade2 = presetsByGrade[2];

  const g1AddTen = grade1.addition.find((candidate) => candidate.id === 'g1-add-10');
  assert.equal(g1AddTen.buildParams().result_max, 10);

  const g1AddTwenty = grade1.addition.find((candidate) => candidate.id === 'g1-add-20');
  assert.equal(g1AddTwenty.buildParams().result_max, 20);

  const g1SubTen = grade1.subtraction.find((candidate) => candidate.id === 'g1-sub-10');
  assert.equal(g1SubTen.buildParams().result_max, 10);

  const g1SubTwenty = grade1.subtraction.find((candidate) => candidate.id === 'g1-sub-20');
  assert.equal(g1SubTwenty.buildParams().result_max, 20);

  const g2SubTwoDigit = grade2.subtraction.find((candidate) => candidate.id === 'g2-sub-2digit');
  assert.equal(g2SubTwoDigit.buildParams({ carryMode: 'mixed' }).result_max, 100);
});

test('grade 1 addition drills expose a 繰り上がり setting (issue #305)', () => {
  const grade1 = presetsByGrade[1];

  const g1AddTen = grade1.addition.find((candidate) => candidate.id === 'g1-add-10');
  const tenCarry = g1AddTen.settings.find((setting) => setting.id === 'carryMode');
  assert.ok(tenCarry, 'g1-add-10 must carry a carryMode setting');
  assert.equal(tenCarry.type, 'fixed');
  assert.equal(tenCarry.valueLabelKey, 'setting_option_none');
  assert.deepEqual(g1AddTen.buildParams(), {
    command_type: 'ope', operator: ['add'], carry_mode: 'none',
    a_min: 1, a_max: 9, b_min: 1, b_max: 9, result_max: 10,
  });

  const g1AddTwenty = grade1.addition.find((candidate) => candidate.id === 'g1-add-20');
  const twentyCarry = g1AddTwenty.settings.find((setting) => setting.id === 'carryMode');
  assert.ok(twentyCarry, 'g1-add-20 must carry a carryMode setting');
  assert.equal(twentyCarry.type, 'choice');
  assert.deepEqual(twentyCarry.options.map((option) => option.value), ['none', 'required', 'mixed']);

  // あり: classic 1-digit + 1-digit carrying, capped at 20.
  assert.deepEqual(g1AddTwenty.buildParams({ carryMode: 'required' }), {
    command_type: 'ope', operator: ['add'], carry_mode: 'required',
    a_min: 1, a_max: 9, b_min: 1, b_max: 9, result_max: 20,
  });
  // なし: no carrying, addend A widened to 1..19 so 1桁+1桁 and 2桁+1桁 mix.
  assert.deepEqual(g1AddTwenty.buildParams({ carryMode: 'none' }), {
    command_type: 'ope', operator: ['add'], carry_mode: 'none',
    a_min: 1, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
  });
  // まぜる: carry unconstrained (carry_mode omitted for the single operator),
  // same widened addend-A range.
  assert.deepEqual(g1AddTwenty.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope', operator: ['add'],
    a_min: 1, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
  });
  // no-arg call (used by the result_max self-documentation test) defaults to まぜる.
  assert.equal(g1AddTwenty.buildParams().result_max, 20);
  assert.equal(g1AddTwenty.buildParams().carry_mode, undefined);
});

test('grade 1 subtraction drills expose a 繰り下がり setting (issue #307)', () => {
  const grade1 = presetsByGrade[1];

  const g1SubTen = grade1.subtraction.find((candidate) => candidate.id === 'g1-sub-10');
  const tenBorrow = g1SubTen.settings.find((setting) => setting.id === 'carryMode');
  assert.ok(tenBorrow, 'g1-sub-10 must carry a carryMode setting');
  assert.equal(tenBorrow.type, 'fixed');
  assert.equal(tenBorrow.valueLabelKey, 'setting_option_none');
  // inactive なし: borrowing is excluded, so no 10-6 type problems.
  assert.deepEqual(g1SubTen.buildParams(), {
    command_type: 'ope', operator: ['sub'], carry_mode: 'none',
    a_min: 2, a_max: 10, b_min: 1, b_max: 9, result_max: 10,
  });

  const g1SubTwenty = grade1.subtraction.find((candidate) => candidate.id === 'g1-sub-20');
  const twentyBorrow = g1SubTwenty.settings.find((setting) => setting.id === 'carryMode');
  assert.ok(twentyBorrow, 'g1-sub-20 must carry a carryMode setting');
  assert.equal(twentyBorrow.type, 'choice');
  assert.deepEqual(twentyBorrow.options.map((option) => option.value), ['none', 'required', 'mixed']);

  // あり: classic 繰り下がり from a 10-19 minuend, capped at 20.
  assert.deepEqual(g1SubTwenty.buildParams({ carryMode: 'required' }), {
    command_type: 'ope', operator: ['sub'], carry_mode: 'required',
    a_min: 10, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
  });
  // なし: no borrowing, minuend widened to 2..19 so 1桁 and 2桁 minuends mix.
  assert.deepEqual(g1SubTwenty.buildParams({ carryMode: 'none' }), {
    command_type: 'ope', operator: ['sub'], carry_mode: 'none',
    a_min: 2, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
  });
  // まぜる: borrow unconstrained (carry_mode omitted for the single operator),
  // same widened minuend range.
  assert.deepEqual(g1SubTwenty.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope', operator: ['sub'],
    a_min: 2, a_max: 19, b_min: 1, b_max: 9, result_max: 20,
  });
  // no-arg call (used by the result_max self-documentation test) defaults to まぜる.
  assert.equal(g1SubTwenty.buildParams().result_max, 20);
  assert.equal(g1SubTwenty.buildParams().carry_mode, undefined);
});

test('grade 1 three-term drill offers add-only / sub-only / mixed operators (issue #309)', () => {
  const item = presetsByGrade[1]['four-operations'].find((candidate) => candidate.id === 'g1-three-terms');
  assert.ok(item, 'g1-three-terms must exist');

  const operators = item.settings.find((setting) => setting.id === 'operators');
  assert.ok(operators, 'g1-three-terms must carry an operators setting');
  assert.equal(operators.type, 'choice');
  // 引き算のみ sits between 足し算のみ and 足し引き混合.
  assert.deepEqual(operators.options.map((option) => option.value), ['add', 'sub', 'addsub']);
  assert.deepEqual(
    operators.options.map((option) => option.labelKey),
    ['setting_option_add_only', 'setting_option_sub_only', 'setting_option_addsub_mixed'],
  );
  assert.equal(operators.default, 'addsub');

  const base = { command_type: 'ope', terms: 3, a_min: 1, a_max: 9, b_min: 1, b_max: 9 };
  // 足し算のみ: single operator, no mixed_operators.
  assert.deepEqual(item.buildParams({ operators: 'add' }), { ...base, operator: ['add'] });
  // 引き算のみ: single operator, no mixed_operators (mirrors the add-only branch).
  assert.deepEqual(item.buildParams({ operators: 'sub' }), { ...base, operator: ['sub'] });
  // 足し引き混合: two operators, mixed_operators enabled.
  assert.deepEqual(item.buildParams({ operators: 'addsub' }), {
    ...base, operator: ['add', 'sub'], mixed_operators: true,
  });
  // unset state falls back to the 足し引き混合 default.
  assert.deepEqual(item.buildParams(), { ...base, operator: ['add', 'sub'], mixed_operators: true });

  // example chips track the chosen operator mode.
  assert.ok(typeof item.examplesFor === 'function', 'g1-three-terms must expose examplesFor');
  assert.ok(item.examplesFor({ operators: 'add' }).every((example) => !example.includes('-')));
  assert.ok(item.examplesFor({ operators: 'sub' }).every((example) => !example.includes('+')));
  assert.deepEqual(item.examplesFor({ operators: 'addsub' }), item.examples);
  assert.deepEqual(item.examplesFor(), item.examples);
});

test('grade 2 basic addition caps the answer at 100 (issue #176)', () => {
  const item = presetsByGrade[2].addition.find((candidate) => candidate.id === 'g2-add-2digit');

  assert.ok(item);
  assert.deepEqual(item.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope',
    operator: ['add'],
    a_min: 1,
    a_max: 99,
    b_min: 1,
    b_max: 99,
    result_max: 100,
  });
});

test('grade 2 advanced addition caps the answer at 1,000', () => {
  const item = presetsByGrade[2].addition.find((candidate) => candidate.id === 'g2-add-result-1000');

  assert.ok(item);
  assert.equal(item.difficultyKey, 'difficulty_advanced');
  assert.equal(item.latexOnly, true);
  assert.deepEqual(item.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope',
    operator: ['add'],
    a_min: 1,
    a_max: 999,
    b_min: 1,
    b_max: 999,
    result_max: 1000,
  });
});

test('grade 2 advanced subtraction caps the answer at 1,000', () => {
  const item = presetsByGrade[2].subtraction.find((candidate) => candidate.id === 'g2-sub-result-1000');

  assert.ok(item);
  assert.equal(item.difficultyKey, 'difficulty_advanced');
  assert.equal(item.latexOnly, true);
  assert.deepEqual(item.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope',
    operator: ['sub'],
    a_min: 1,
    a_max: 999,
    b_min: 1,
    b_max: 999,
    result_max: 1000,
  });
});

test('grade 3 advanced addition caps the answer at 10,000', () => {
  const item = presetsByGrade[3].addition.find((candidate) => candidate.id === 'g3-add-result-10000');

  assert.ok(item);
  assert.equal(item.difficultyKey, 'difficulty_advanced');
  assert.equal(item.latexOnly, true);
  assert.deepEqual(item.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope',
    operator: ['add'],
    a_min: 1,
    a_max: 9999,
    b_min: 1,
    b_max: 9999,
    result_max: 10000,
  });
});

test('grade 3 advanced subtraction caps the answer at 10,000', () => {
  const item = presetsByGrade[3].subtraction.find((candidate) => candidate.id === 'g3-sub-result-10000');

  assert.ok(item);
  assert.equal(item.difficultyKey, 'difficulty_advanced');
  assert.equal(item.latexOnly, true);
  assert.deepEqual(item.buildParams({ carryMode: 'mixed' }), {
    command_type: 'ope',
    operator: ['sub'],
    a_min: 1,
    a_max: 9999,
    b_min: 1,
    b_max: 9999,
    result_max: 10000,
  });
});

test('grade 2 three-term drill offers add-only / sub-only / mixed operators (issue #311)', () => {
  const item = presetsByGrade[2]['four-operations'].find((candidate) => candidate.id === 'g2-addsub-mixed');
  assert.ok(item, 'g2-addsub-mixed must exist');

  const operators = item.settings.find((setting) => setting.id === 'operators');
  assert.ok(operators, 'g2-addsub-mixed must carry an operators setting');
  assert.equal(operators.type, 'choice');
  // 引き算のみ sits between 足し算のみ and 足し引き混合 (mirrors g1-three-terms).
  assert.deepEqual(operators.options.map((option) => option.value), ['add', 'sub', 'addsub']);
  assert.deepEqual(
    operators.options.map((option) => option.labelKey),
    ['setting_option_add_only', 'setting_option_sub_only', 'setting_option_addsub_mixed'],
  );
  assert.equal(operators.default, 'addsub');

  const base = { command_type: 'ope', terms: 3, a_min: 1, a_max: 99, b_min: 1, b_max: 99 };
  // 足し算のみ: single operator, no mixed_operators.
  assert.deepEqual(item.buildParams({ operators: 'add' }), { ...base, operator: ['add'] });
  // 引き算のみ: single operator, no mixed_operators (mirrors the add-only branch).
  assert.deepEqual(item.buildParams({ operators: 'sub' }), { ...base, operator: ['sub'] });
  // 足し引き混合: two operators, mixed_operators enabled.
  assert.deepEqual(item.buildParams({ operators: 'addsub' }), {
    ...base, operator: ['add', 'sub'], mixed_operators: true,
  });
  // unset state falls back to the 足し引き混合 default.
  assert.deepEqual(item.buildParams(), { ...base, operator: ['add', 'sub'], mixed_operators: true });

  // example chips track the chosen operator mode.
  assert.ok(typeof item.examplesFor === 'function', 'g2-addsub-mixed must expose examplesFor');
  assert.ok(item.examplesFor({ operators: 'add' }).every((example) => !example.includes('-')));
  assert.ok(item.examplesFor({ operators: 'sub' }).every((example) => !example.includes('+')));
  assert.deepEqual(item.examplesFor({ operators: 'addsub' }), item.examples);
  assert.deepEqual(item.examplesFor(), item.examples);
});

test('grade 3 four-operations mix caps the answer at 1,000 without multiplication', () => {
  const item = presetsByGrade[3]['four-operations'].find((candidate) => candidate.id === 'g3-addsub-mixed-result-1000');

  assert.ok(item);
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope',
    operator: ['add', 'sub'],
    terms: 3,
    mixed_operators: true,
    a_min: 1,
    a_max: 999,
    b_min: 1,
    b_max: 999,
    result_max: 1000,
  });
});

test('grade 3 parenthesized mix caps the answer at 1,000 and multiplication operands at 2 digits', () => {
  const item = presetsByGrade[3]['four-operations'].find((candidate) => candidate.id === 'g3-parentheses-mul-result-1000');

  assert.ok(item);
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope',
    operator: ['add', 'sub', 'mul'],
    terms: 3,
    mixed_operators: true,
    use_parentheses: true,
    a_min: 1,
    a_max: 99,
    b_min: 1,
    b_max: 99,
    result_max: 1000,
  });
});

test('grade 3 fraction items live under addition/subtraction, not a separate fraction category', () => {
  assert.equal(presetsByGrade[3].fraction, undefined);
  assert.ok(presetsByGrade[3].addition.some((item) => item.id === 'g3-fraction-add'));
  assert.ok(presetsByGrade[3].subtraction.some((item) => item.id === 'g3-fraction-sub'));
});

test('grade 6 fraction mul/div items support reducible_mode and are marked full (#114)', () => {
  const ids = [
    'g6-fraction-mul-int', 'g6-int-mul-fraction', 'g6-fraction-mul',
    'g6-fraction-div-int', 'g6-int-div-fraction', 'g6-fraction-div',
  ];
  for (const id of ids) {
    const item = presetsByGrade[6].fraction.find((candidate) => candidate.id === id);
    const context = `grade 6 / fraction / ${id}`;

    assert.ok(item, `${context}: item must exist`);
    assert.equal(item.supportLevel, 'full', `${context}: supportLevel must be 'full'`);
    assert.equal(item.buildParams({ reduction: 'required' }).reducible_mode, 'required', context);
    assert.equal(item.buildParams({ reduction: 'none' }).reducible_mode, 'none', context);
    assert.equal(item.buildParams({ reduction: 'mixed' }).reducible_mode, 'mixed', context);
    assert.equal(item.buildParams({}).reducible_mode, 'mixed', `${context}: unset state defaults to 'mixed'`);
  }
});

test('grade 2 kuku keeps mixed rows random and ignores the question-order state', () => {
  const item = presetsByGrade[2].multiplication.find((candidate) => candidate.id === 'g2-kuku');
  const expected = { command_type: 'ope', operator: ['mul'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 };

  assert.deepEqual(item.buildParams({ dan: 'mixed', questionOrder: 'ascending' }), expected);
  assert.deepEqual(item.buildParams({ dan: 'mixed', questionOrder: 'descending' }), expected);
  assert.deepEqual(item.buildParams({ dan: 'mixed', questionOrder: 'random' }), expected);
});

test('menu item ids are unique across the entire data model', () => {
  const ids = allItems().map(({ item }) => item.id);
  assert.equal(ids.length, new Set(ids).size, 'duplicate id found in drillPresets.js');
});

test('buildParams(defaultState) returns a request body with paper_size-ready fields', () => {
  for (const { gradeKey, category, item } of allItems()) {
    const params = item.buildParams(defaultSettingsState(item.settings));
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    assert.equal(typeof params, 'object', `${context}: buildParams must return an object`);
    assert.equal(typeof params.command_type, 'string', `${context}: params.command_type must be a string`);
  }
});

test('examplesFor(defaultState) matches the static examples array (issue #135)', () => {
  for (const { gradeKey, category, item } of allItems()) {
    if (!item.examplesFor) continue;
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    assert.deepEqual(item.examplesFor(defaultSettingsState(item.settings)), item.examples, context);
  }
});

test('examplesFor returns a non-empty array of non-empty strings for every option of every choice setting', () => {
  for (const { gradeKey, category, item } of allItems()) {
    if (!item.examplesFor) continue;
    const defaultState = defaultSettingsState(item.settings);
    for (const setting of item.settings) {
      if (setting.type !== 'choice') continue;
      for (const option of setting.options) {
        const context = `grade ${gradeKey} / ${category} / ${item.id} / ${setting.id}=${option.value}`;
        const state = { ...defaultState, [setting.id]: option.value };
        const examples = item.examplesFor(state);
        assert.ok(Array.isArray(examples) && examples.length > 0, `${context}: examplesFor must return a non-empty array`);
        for (const example of examples) {
          assert.equal(typeof example, 'string', `${context}: each example must be a string`);
          assert.ok(example.length > 0, `${context}: each example must be non-empty`);
        }
      }
    }
  }
});

// The exact set of items 出題形式(式/筆算, issue #134) was added to:
// grade2/3/4's plain-integer or symmetric-decimal-places add/sub/mul/div
// items (--vertical-compatible in nuts_calc_tex.py), plus grade5's
// decimal-by-decimal multiplication. Explicitly enumerated (not derived by
// scanning for compatible items) per the issue's scope decision.
const DISPLAY_FORMAT_ITEM_IDS = [
  'g2-add-2digit', 'g2-add-result-1000', 'g2-sub-2digit', 'g2-sub-result-1000',
  'g3-add-result-10000', 'g3-decimal-addsub', 'g3-sub-result-10000', 'g3-decimal-sub',
  'g3-mul-2x1', 'g3-mul-3x1', 'g3-mul-2x2',
  'g4-decimal-add', 'g4-decimal-sub', 'g4-decimal-mul-int',
  'g4-div-1digit', 'g4-div-2digit', 'g4-decimal-div-int',
  'g5-decimal-mul',
];

test('exactly the enumerated 18 items carry a displayFormat setting (issue #134)', () => {
  const actualIds = allItems()
    .filter(({ item }) => item.settings.some((setting) => setting.id === 'displayFormat'))
    .map(({ item }) => item.id)
    .sort();
  assert.deepEqual(actualIds, [...DISPLAY_FORMAT_ITEM_IDS].sort());
});

test('displayFormat defaults to horizontal (no vertical field) for every displayFormat item', () => {
  for (const { gradeKey, category, item } of allItems()) {
    if (!DISPLAY_FORMAT_ITEM_IDS.includes(item.id)) continue;
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    const params = item.buildParams(defaultSettingsState(item.settings));
    assert.equal(params.vertical, undefined, `${context}: default state must not set vertical`);
  }
});

test('displayFormat: written sets vertical: true in buildParams for every displayFormat item', () => {
  for (const { gradeKey, category, item } of allItems()) {
    if (!DISPLAY_FORMAT_ITEM_IDS.includes(item.id)) continue;
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    const state = { ...defaultSettingsState(item.settings), displayFormat: 'written' };
    const params = item.buildParams(state);
    assert.equal(params.vertical, true, `${context}: displayFormat: written must set vertical: true`);
    assert.equal(params.command_type, 'ope', `${context}: --vertical is only implemented for the 'ope' command`);
  }
});

test('displayFormat setting options are labeled 式 (horizontal) and 筆算 (written)', () => {
  for (const { gradeKey, category, item } of allItems()) {
    if (!DISPLAY_FORMAT_ITEM_IDS.includes(item.id)) continue;
    const context = `grade ${gradeKey} / ${category} / ${item.id}`;
    const setting = item.settings.find((candidate) => candidate.id === 'displayFormat');
    assert.equal(setting.default, 'horizontal', context);
    assert.deepEqual(
      setting.options.map((option) => option.value).sort(),
      ['horizontal', 'written'],
      context,
    );
  }
});
