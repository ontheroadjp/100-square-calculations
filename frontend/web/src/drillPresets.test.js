import { test } from 'node:test';
import assert from 'node:assert/strict';
import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';

const KNOWN_CATEGORIES = new Set([
  'addition', 'subtraction', 'multiplication', 'division',
  'decimal', 'fraction', 'four-operations', 'number-sense',
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

  // issue #331: the four grade-1 no-carry/no-borrow drills within 100 join the
  // same "Nまでの" self-documentation family.
  for (const id of ['g1-add-tens', 'g1-add-100']) {
    assert.equal(grade1.addition.find((candidate) => candidate.id === id).buildParams().result_max, 100);
  }
  for (const id of ['g1-sub-tens', 'g1-sub-100']) {
    assert.equal(grade1.subtraction.find((candidate) => candidate.id === id).buildParams().result_max, 100);
  }
});

test('grade 1 no-carry / no-borrow drills within 100 for 何十±何十 and 2桁±1桁 (issue #331)', () => {
  const grade1 = presetsByGrade[1];

  assert.deepEqual(
    grade1.addition.map((item) => item.id),
    ['g1-add-10', 'g1-add-20', 'g1-add-tens', 'g1-add-100'],
    'grade 1 addition order',
  );
  assert.deepEqual(
    grade1.subtraction.map((item) => item.id),
    ['g1-sub-10', 'g1-sub-20', 'g1-sub-tens', 'g1-sub-100'],
    'grade 1 subtraction order',
  );

  const cases = [
    {
      category: 'addition', id: 'g1-add-tens', difficulty: 'difficulty_basic', borrowLabel: 'setting_carry_label',
      params: {
        command_type: 'ope', operator: ['add'], carry_mode: 'none',
        a_min: 10, a_max: 90, b_min: 10, b_max: 90, a_multiple: 10, b_multiple: 10, result_max: 100,
      },
    },
    {
      category: 'addition', id: 'g1-add-100', difficulty: 'difficulty_standard', borrowLabel: 'setting_carry_label',
      params: {
        command_type: 'ope', operator: ['add'], carry_mode: 'none',
        a_min: 10, a_max: 99, b_min: 1, b_max: 9, result_max: 100,
      },
    },
    {
      category: 'subtraction', id: 'g1-sub-tens', difficulty: 'difficulty_basic', borrowLabel: 'setting_borrow_label',
      params: {
        command_type: 'ope', operator: ['sub'], carry_mode: 'none',
        a_min: 10, a_max: 90, b_min: 10, b_max: 90, a_multiple: 10, b_multiple: 10, result_max: 100,
      },
    },
    {
      category: 'subtraction', id: 'g1-sub-100', difficulty: 'difficulty_standard', borrowLabel: 'setting_borrow_label',
      params: {
        command_type: 'ope', operator: ['sub'], carry_mode: 'none',
        a_min: 10, a_max: 99, b_min: 1, b_max: 9, result_max: 100,
      },
    },
  ];

  for (const { category, id, difficulty, borrowLabel, params } of cases) {
    const item = grade1[category].find((candidate) => candidate.id === id);
    const context = `grade 1 / ${category} / ${id}`;

    assert.ok(item, `${context}: item must exist`);
    assert.equal(item.difficultyKey, difficulty, `${context}: difficultyKey`);
    assert.equal(item.supportLevel, 'full', `${context}: supportLevel`);
    assert.equal(item.latexOnly, true, `${context}: latexOnly`);
    assert.equal(item.examplesFor, undefined, `${context}: no examplesFor (fixed setting only)`);

    assert.equal(item.settings.length, 1, `${context}: exactly one setting`);
    const [setting] = item.settings;
    assert.equal(setting.type, 'fixed', `${context}: setting is fixed/inactive`);
    assert.equal(setting.id, 'carryMode', `${context}: setting id`);
    assert.equal(setting.labelKey, borrowLabel, `${context}: setting labelKey`);
    assert.equal(setting.valueLabelKey, 'setting_option_none', `${context}: shows なし`);
    assert.deepEqual(
      setting.options.map((option) => option.value),
      ['none', 'required', 'mixed'],
      `${context}: renders the full なし/あり/まぜる control disabled`,
    );

    assert.deepEqual(item.buildParams(), params, `${context}: buildParams`);
    assert.equal(item.buildParams().carry_mode, 'none', `${context}: carry_mode none`);
  }

  // Only the 何十 items carry the multiples-of-10 constraint.
  assert.equal(grade1.addition.find((i) => i.id === 'g1-add-tens').buildParams().a_multiple, 10);
  assert.equal(grade1.addition.find((i) => i.id === 'g1-add-tens').buildParams().b_multiple, 10);
  assert.equal('a_multiple' in grade1.addition.find((i) => i.id === 'g1-add-100').buildParams(), false);
  assert.equal('a_multiple' in grade1.subtraction.find((i) => i.id === 'g1-sub-100').buildParams(), false);
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

test('grade 4 decimal×integer multiplication is integer-multiplier only (issue #329)', () => {
  const item = presetsByGrade[4].multiplication.find((candidate) => candidate.id === 'g4-decimal-mul-int');
  assert.ok(item, 'g4-decimal-mul-int must exist');
  assert.equal(item.titleKey, 'menu_g4_decimal_mul_int_title');

  // 学習指導要領 第4学年「小数」covers only the integer-multiplier case; the
  // #313 factorOrder choice (整数×小数 / まぜる make the multiplier a decimal,
  // a grade 5 topic) is removed. The multiplier is a fixed, disabled 整数 pill.
  assert.equal(item.settings.find((setting) => setting.id === 'factorOrder'), undefined);
  const multiplier = item.settings[0];
  assert.equal(multiplier.id, 'multiplier');
  assert.equal(multiplier.type, 'fixed');
  assert.equal(multiplier.valueLabelKey, 'setting_option_integer');
  assert.equal(item.settings[1].id, 'displayFormat');

  // buildParams always yields 小数(第1位) × 整数, regardless of state.
  const expected = {
    command_type: 'ope', operator: ['mul'], a_digits: 2, b_digits: 1, a_decimal_places: 1,
  };
  assert.deepEqual(item.buildParams(), expected);
  assert.deepEqual(item.buildParams({}), expected);
  // Stale persisted factorOrder values are ignored (no int_decimal / mixed branch).
  assert.deepEqual(item.buildParams({ factorOrder: 'int_decimal' }), expected);
  assert.deepEqual(item.buildParams({ factorOrder: 'mixed' }), expected);
  assert.equal(item.buildParams({}).mixed_decimal_operand_order, undefined);

  // displayFormat: written still adds vertical: true.
  assert.deepEqual(item.buildParams({ displayFormat: 'written' }), { ...expected, vertical: true });

  // No per-choice example sets; every static example is 小数×整数.
  assert.equal(item.examplesFor, undefined);
  assert.ok(item.examples.every((example) => /^\d+\.\d+×\d+$/.test(example)));
});

test('grade 5 groups 小数×小数 / 整数と小数の割り算 under a dedicated decimal category, not multiplication/division (issue #320)', () => {
  assert.equal(presetsByGrade[5].multiplication, undefined);
  assert.equal(presetsByGrade[5].division, undefined);
  assert.deepEqual(
    presetsByGrade[5].decimal.map((item) => item.id),
    ['g5-decimal-mul', 'g5-decimal-div', 'g5-decimal-div-remainder'],
  );
  // The 小数の四則混合計算 drill stays in four-operations.
  assert.ok(presetsByGrade[5]['four-operations'].some((item) => item.id === 'g5-decimal-four-ops'));
});

test('grade 5 decimal division offers 整数÷小数 / 小数÷小数 / まぜる dividend selection (issue #317)', () => {
  const item = presetsByGrade[5].decimal.find((candidate) => candidate.id === 'g5-decimal-div');
  assert.ok(item, 'g5-decimal-div must exist');
  assert.equal(item.titleKey, 'menu_g5_decimal_div_title');

  const dividendType = item.settings.find((setting) => setting.id === 'dividendType');
  assert.ok(dividendType, 'g5-decimal-div must carry a dividendType setting');
  assert.equal(dividendType.type, 'choice');
  assert.deepEqual(
    dividendType.options.map((option) => option.value),
    ['integer_div_decimal', 'decimal_div_decimal', 'mixed'],
  );
  assert.deepEqual(
    dividendType.options.map((option) => option.labelKey),
    ['setting_option_integer_div_decimal', 'setting_option_decimal_div_decimal', 'setting_option_mixed'],
  );
  assert.equal(dividendType.default, 'mixed');

  // 整数÷小数: whole-number dividend (a_decimal_places 0), decimal divisor, --integer-dividend.
  assert.deepEqual(item.buildParams({ dividendType: 'integer_div_decimal' }), {
    command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2,
    b_decimal_places: 1, a_decimal_places: 0, dividend_mode: 'integer',
  });
  // 小数÷小数: unchanged from before #317 (no dividend_mode flag).
  assert.deepEqual(item.buildParams({ dividendType: 'decimal_div_decimal' }), {
    command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2,
    b_decimal_places: 1, a_decimal_places: 1,
  });
  // まぜる (default): backend mixes the dividend kind per problem.
  const mixedExpected = {
    command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2,
    b_decimal_places: 1, a_decimal_places: 1, dividend_mode: 'mixed',
  };
  assert.deepEqual(item.buildParams({ dividendType: 'mixed' }), mixedExpected);
  assert.deepEqual(item.buildParams(), mixedExpected);
  assert.deepEqual(item.buildParams({}), mixedExpected);

  // example chips track the chosen dividend kind.
  assert.deepEqual(item.examplesFor({ dividendType: 'mixed' }), item.examples);
  assert.ok(item.examplesFor({ dividendType: 'integer_div_decimal' }).every((example) => /^\d+÷\d+\.\d/.test(example)));
  assert.ok(item.examplesFor({ dividendType: 'decimal_div_decimal' }).every((example) => /^\d+\.\d+÷\d+\.\d/.test(example)));
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

test('grade 3 division includes an exact two-digit-quotient drill faithful to the Course of Study (issue #332)', () => {
  const item = presetsByGrade[3].division.find((candidate) => candidate.id === 'g3-div-2digit-quotient');

  assert.ok(item, 'g3-div-2digit-quotient must exist in grade 3 division');
  assert.equal(item.difficultyKey, 'difficulty_standard');
  assert.equal(item.supportLevel, 'full');
  assert.equal(item.latexOnly, true);
  assert.equal(item.titleKey, 'menu_g3_div_2digit_quotient_title');

  const remainder = item.settings.find((setting) => setting.id === 'remainderMode');
  assert.equal(remainder.type, 'fixed');
  assert.equal(remainder.valueLabelKey, 'setting_option_none');

  // Full 1-digit divisor range (b 2..9); the backend --quotient-digits flag
  // (mapped from quotient_digits) enforces the 2-digit quotient, not the a/b
  // ranges. Distinct from g3-div-kuku (single-digit 九九 quotients).
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope', operator: ['div'], remainder_mode: 'none',
    a_min: 20, a_max: 99, b_min: 2, b_max: 9, quotient_digits: 2,
  });
});

test('grade 4 division includes a 小数÷整数 decimal-remainder drill (issue #333)', () => {
  const item = presetsByGrade[4].division.find((candidate) => candidate.id === 'g4-decimal-div-int-remainder');

  assert.ok(item, 'g4-decimal-div-int-remainder must exist in grade 4 division');
  assert.equal(item.difficultyKey, 'difficulty_standard');
  assert.equal(item.supportLevel, 'full');
  assert.equal(item.latexOnly, true);
  assert.equal(item.titleKey, 'menu_g4_decimal_div_int_remainder_title');

  // Two fixed pills: 除数：整数 and 余り：あり (the drill is always あまり --
  // 商を一の位まで求めてあまりを出す).
  const divisor = item.settings.find((setting) => setting.id === 'divisor');
  assert.equal(divisor.type, 'fixed');
  assert.equal(divisor.valueLabelKey, 'setting_option_integer');
  const remainder = item.settings.find((setting) => setting.id === 'remainder');
  assert.equal(remainder.type, 'fixed');
  assert.equal(remainder.valueLabelKey, 'setting_option_required');

  // decimal_remainder (snake_case = nuts_calc_tex.py --decimal-remainder) drives
  // the non-exact division; a decimal dividend (a_decimal_places: 1) over a
  // whole-number divisor (b 2..9). No displayFormat setting: the backend rejects
  // --vertical --decimal-remainder, so this id must NOT be in DISPLAY_FORMAT_ITEM_IDS.
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope', operator: ['div'],
    a_digits: 2, b_min: 2, b_max: 9, a_decimal_places: 1,
    decimal_remainder: true,
  });
  assert.ok(!DISPLAY_FORMAT_ITEM_IDS.includes(item.id));
  assert.ok(!item.settings.some((setting) => setting.id === 'displayFormat'));
});

test('grade 5 decimal category includes a 小数÷小数 decimal-remainder drill (issue #334)', () => {
  const item = presetsByGrade[5].decimal.find((candidate) => candidate.id === 'g5-decimal-div-remainder');

  assert.ok(item, 'g5-decimal-div-remainder must exist in grade 5 decimal');
  assert.equal(item.difficultyKey, 'difficulty_standard');
  assert.equal(item.supportLevel, 'full');
  assert.equal(item.latexOnly, true);
  assert.equal(item.titleKey, 'menu_g5_decimal_div_remainder_title');

  // Two fixed pills: 除数：小数 and 余り：あり. The drill is always あまり --
  // わる数を整数に直して商を一の位まで求め、あまりを小数で出す (grade 5
  // 小数のわり算). Distinct from the untouched #317 exact-quotient g5-decimal-div.
  const divisor = item.settings.find((setting) => setting.id === 'divisor');
  assert.equal(divisor.type, 'fixed');
  assert.equal(divisor.valueLabelKey, 'setting_option_decimal');
  const remainder = item.settings.find((setting) => setting.id === 'remainder');
  assert.equal(remainder.type, 'fixed');
  assert.equal(remainder.valueLabelKey, 'setting_option_required');

  // decimal_remainder (snake_case = nuts_calc_tex.py --decimal-remainder) over a
  // decimal dividend (a_decimal_places: 1) AND a decimal divisor
  // (b_decimal_places: 1) -- the backend scales the divisor up to a whole
  // number before dividing (issue #334). No displayFormat setting: the backend
  // rejects --vertical --decimal-remainder, so this id must NOT be in
  // DISPLAY_FORMAT_ITEM_IDS.
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope', operator: ['div'],
    a_digits: 2, b_digits: 2, a_decimal_places: 1, b_decimal_places: 1,
    decimal_remainder: true,
  });
  assert.ok(!DISPLAY_FORMAT_ITEM_IDS.includes(item.id));
  assert.ok(!item.settings.some((setting) => setting.id === 'displayFormat'));

  // g5-decimal-div (#317, exact quotient) is untouched: still a single
  // dividendType choice setting, no decimal_remainder.
  const exact = presetsByGrade[5].decimal.find((candidate) => candidate.id === 'g5-decimal-div');
  assert.ok(exact.settings.some((setting) => setting.id === 'dividendType'));
  assert.equal(exact.buildParams({ dividendType: 'decimal_div_decimal' }).decimal_remainder, undefined);
});

test('grade 4 number-sense includes a 概数 drill with a round / estimate kind selector (issue #346)', () => {
  const item = presetsByGrade[4]['number-sense'].find((candidate) => candidate.id === 'g4-approx');

  assert.ok(item, 'g4-approx must exist in grade 4 number-sense');
  assert.equal(item.difficultyKey, 'difficulty_standard');
  assert.equal(item.supportLevel, 'full');
  assert.equal(item.latexOnly, true);
  assert.equal(item.titleKey, 'menu_g4_approx_title');

  const kind = item.settings.find((setting) => setting.id === 'approxKind');
  assert.equal(kind.type, 'choice');
  assert.deepEqual(kind.options.map((option) => option.value), ['round', 'estimate']);
  assert.equal(kind.default, 'round');

  // kind=round sends no operator (nuts_calc_tex.py ignores it) and no operand
  // ranges (resolve_approx_params fills the per-kind APPROX_DEFAULT_* ranges).
  assert.deepEqual(item.buildParams({ approxKind: 'round' }), {
    command_type: 'approx', kind: 'round',
  });
  // kind=estimate forwards the chosen operator as a single-element list.
  assert.deepEqual(item.buildParams({ approxKind: 'estimate', approxOperator: 'div' }), {
    command_type: 'approx', kind: 'estimate', operator: ['div'],
  });
  assert.deepEqual(item.buildParams(), { command_type: 'approx', kind: 'round' });

  // No displayFormat (筆算) setting -- this is an arrow-style ≒ conversion.
  assert.ok(!DISPLAY_FORMAT_ITEM_IDS.includes(item.id));
  assert.ok(!item.settings.some((setting) => setting.id === 'displayFormat'));
});

test('grade 5 number-sense includes a 商をがい数で表す drill backed by approx --kind quotient (issue #346)', () => {
  const item = presetsByGrade[5]['number-sense'].find((candidate) => candidate.id === 'g5-approx-quotient');

  assert.ok(item, 'g5-approx-quotient must exist in grade 5 number-sense');
  assert.equal(item.difficultyKey, 'difficulty_standard');
  assert.equal(item.supportLevel, 'full');
  assert.equal(item.latexOnly, true);
  assert.equal(item.titleKey, 'menu_g5_approx_quotient_title');

  const kind = item.settings.find((setting) => setting.id === 'approxKind');
  assert.equal(kind.type, 'fixed');
  assert.equal(kind.valueLabelKey, 'setting_option_approx_quotient_kind');

  assert.deepEqual(item.buildParams(), {
    command_type: 'approx', kind: 'quotient',
    dividend_decimal_places: 1, quotient_decimal_places: 2,
  });
  assert.ok(!DISPLAY_FORMAT_ITEM_IDS.includes(item.id));
});

test('grade 4 four-operations consolidates parentheses drills to two tiers: basic ＋− and standard ＋−×÷ (#340)', () => {
  const items = presetsByGrade[4]['four-operations'];
  const parenthesesItems = items.filter((candidate) => candidate.id.includes('parentheses'));

  assert.deepEqual(
    parenthesesItems.map((candidate) => candidate.id),
    ['g4-parentheses-addsub', 'g4-parentheses'],
  );
  // difficulty_basic renders as 基礎, difficulty_standard as 標準 (strings.ja.json).
  assert.deepEqual(
    parenthesesItems.map((candidate) => candidate.difficultyKey),
    ['difficulty_basic', 'difficulty_standard'],
  );
  assert.deepEqual(parenthesesItems[0].buildParams().operator, ['add', 'sub']);
  assert.deepEqual(parenthesesItems[1].buildParams().operator, ['add', 'sub', 'mul', 'div']);
  assert.equal(parenthesesItems[1].buildParams().use_parentheses, true);

  // the redundant middle tier removed in #340 must be gone
  assert.ok(!items.some((candidate) => candidate.id === 'g4-parentheses-mul-result-1000'));
});

test('grade 4 standard parentheses drill forces a non-trivial division per problem (#342)', () => {
  const items = presetsByGrade[4]['four-operations'];
  const standard = items.find((candidate) => candidate.id === 'g4-parentheses');
  const basic = items.find((candidate) => candidate.id === 'g4-parentheses-addsub');

  assert.deepEqual(standard.buildParams(), {
    command_type: 'ope',
    operator: ['add', 'sub', 'mul', 'div'],
    mixed_operators: true,
    use_parentheses: true,
    nontrivial_division: true,
    a_digits: 1,
    b_digits: 1,
  });

  // the add/sub-only basic tier must NOT gain the division flag
  assert.ok(!('nontrivial_division' in basic.buildParams()));

  // static examples match the generator output shape (3 operands / 2
  // operators, parenthesised) and every one shows a division
  assert.deepEqual(standard.examples, ['(8+4)÷3', '8÷(6-4)', '(9÷3)×5']);
  assert.ok(standard.examples.every((example) => example.includes('÷')));
});

test('grade 3 four-operations no longer contains parentheses or multiplication (#328)', () => {
  const items = presetsByGrade[3]['four-operations'];

  assert.deepEqual(items.map((candidate) => candidate.id), ['g3-addsub-mixed-result-1000']);
  for (const item of items) {
    const params = item.buildParams();
    assert.ok(!('use_parentheses' in params), `${item.id} must not use parentheses in grade 3`);
    assert.ok(!params.operator.includes('mul'), `${item.id} must not include multiplication in grade 3`);
  }
});

test('grade 2 four-operations no longer contains parentheses (#330)', () => {
  const items = presetsByGrade[2]['four-operations'];

  assert.deepEqual(items.map((candidate) => candidate.id), ['g2-addsub-mixed']);
  for (const item of items) {
    const params = item.buildParams();
    assert.ok(!('use_parentheses' in params), `${item.id} must not use parentheses in grade 2`);
  }
});

test('grade 4 parentheses add/sub drill is a basic add/sub-only four-operations item (#330)', () => {
  const item = presetsByGrade[4]['four-operations'].find((candidate) => candidate.id === 'g4-parentheses-addsub');

  assert.ok(item, 'g4-parentheses-addsub must exist in grade 4 four-operations');
  // moved from grade 2 (g2-parentheses) and downgraded standard -> basic: it is
  // the plain introduction of the （ ）"compute-inside-first" rule (#330).
  assert.equal(item.difficultyKey, 'difficulty_basic');
  assert.deepEqual(item.buildParams(), {
    command_type: 'ope',
    operator: ['add', 'sub'],
    terms: 3,
    use_parentheses: true,
    a_min: 1,
    a_max: 90,
    b_min: 1,
    b_max: 90,
  });
});

test('grade 3 fraction items live under addition/subtraction, not a separate fraction category', () => {
  assert.equal(presetsByGrade[3].fraction, undefined);
  assert.ok(presetsByGrade[3].addition.some((item) => item.id === 'g3-fraction-add'));
  assert.ok(presetsByGrade[3].subtraction.some((item) => item.id === 'g3-fraction-sub'));
});

test('grade 4 fraction items live under addition/subtraction, not a separate fraction category', () => {
  assert.equal(presetsByGrade[4].fraction, undefined);
  assert.ok(presetsByGrade[4].addition.some((item) => item.id === 'g4-fraction-add'));
  assert.ok(presetsByGrade[4].subtraction.some((item) => item.id === 'g4-fraction-sub'));
});

test('grade 6 fraction mul/div items support reducible_mode and are marked full (#114)', () => {
  // 分数×整数 / 分数÷整数 moved to grade 5 in issue #327; grade 6 keeps the
  // fraction-multiplier/divisor cases plus 分数×分数 / 分数÷分数.
  const ids = [
    'g6-int-mul-fraction', 'g6-fraction-mul',
    'g6-int-div-fraction', 'g6-fraction-div',
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

test('分数×整数 / 分数÷整数 live in the grade 5 fraction category, not grade 6 (issue #327)', () => {
  assert.equal(
    presetsByGrade[6].fraction.find((item) => item.id === 'g6-fraction-mul-int'),
    undefined,
    'g6-fraction-mul-int must be gone from grade 6',
  );
  assert.equal(
    presetsByGrade[6].fraction.find((item) => item.id === 'g6-fraction-div-int'),
    undefined,
    'g6-fraction-div-int must be gone from grade 6',
  );

  const cases = [
    { id: 'g5-fraction-mul-int', operator: 'mul' },
    { id: 'g5-fraction-div-int', operator: 'div' },
  ];
  for (const { id, operator } of cases) {
    const item = presetsByGrade[5].fraction.find((candidate) => candidate.id === id);
    const context = `grade 5 / fraction / ${id}`;

    assert.ok(item, `${context}: item must exist`);
    assert.equal(item.supportLevel, 'full', `${context}: supportLevel must be 'full'`);
    assert.equal(item.latexOnly, true, `${context}: latexOnly must be true`);

    const params = item.buildParams({ reduction: 'mixed' });
    assert.equal(params.command_type, 'mixed', context);
    assert.deepEqual(params.operator, [operator], context);
    assert.deepEqual(params.a_kind, ['fraction'], context);
    assert.deepEqual(params.b_kind, ['int'], context);

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
