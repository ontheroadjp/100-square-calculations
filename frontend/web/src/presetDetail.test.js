import { test } from 'node:test';
import assert from 'node:assert/strict';
import { PROBLEM_COUNT_OPTIONS, layoutForProblemCount, buildSummaryParts } from './presetDetail.js';

test('layoutForProblemCount returns rows/columns for every supported problem count', () => {
  assert.deepEqual(layoutForProblemCount(10), { rows: 5, columns: 2 });
  assert.deepEqual(layoutForProblemCount(20), { rows: 10, columns: 2 });
  assert.deepEqual(layoutForProblemCount(30), { rows: 10, columns: 3 });
});

test('layoutForProblemCount falls back to the 20-problem layout for an unknown count', () => {
  assert.deepEqual(layoutForProblemCount(999), layoutForProblemCount(20));
});

test('every rows/columns layout multiplies out to its problem count', () => {
  for (const count of PROBLEM_COUNT_OPTIONS) {
    const { rows, columns } = layoutForProblemCount(count);
    assert.equal(rows * columns, count, `problem count ${count}`);
  }
});

// Fake translator: prefixes the key so assertions can check exactly what was
// looked up, independent of strings.ja.json's actual Japanese copy.
const translate = (key) => `[${key}]`;

test('buildSummaryParts starts with the problem count and difficulty', () => {
  const parts = buildSummaryParts(
    { problemCount: 20, difficultyKey: 'difficulty_standard', settings: [], settingsState: {} },
    translate,
  );
  assert.deepEqual(parts, ['20[problem_count_unit]', '[difficulty_standard]']);
});

test('buildSummaryParts appends the selected option for a choice setting', () => {
  const settings = [{
    id: 'carryMode', labelKey: 'setting_carry_label', type: 'choice',
    options: [{ value: 'mixed', labelKey: 'setting_option_mixed' }],
    default: 'mixed',
  }];
  const parts = buildSummaryParts(
    { problemCount: 20, difficultyKey: 'difficulty_standard', settings, settingsState: { carryMode: 'mixed' } },
    translate,
  );
  assert.deepEqual(parts.slice(2), ['[setting_carry_label]：[setting_option_mixed]']);
});

test('buildSummaryParts appends the fixed value for a fixed setting', () => {
  const settings = [{ id: 'parentheses', labelKey: 'setting_parentheses_label', type: 'fixed', valueLabelKey: 'setting_option_present' }];
  const parts = buildSummaryParts(
    { problemCount: 30, difficultyKey: 'difficulty_basic', settings, settingsState: {} },
    translate,
  );
  assert.deepEqual(parts.slice(2), ['[setting_parentheses_label]：[setting_option_present]']);
});

test('buildSummaryParts skips a choice setting with no matching option (defensive)', () => {
  const settings = [{
    id: 'dan', labelKey: 'setting_dan_label', type: 'choice',
    options: [{ value: '1', labelKey: 'setting_option_dan_1' }],
    default: '1',
  }];
  const parts = buildSummaryParts(
    { problemCount: 10, difficultyKey: 'difficulty_basic', settings, settingsState: { dan: 'unknown' } },
    translate,
  );
  assert.deepEqual(parts.slice(2), []);
});
