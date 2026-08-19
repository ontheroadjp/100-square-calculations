import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PROBLEM_COUNT_OPTIONS,
  layoutForProblemCount,
  buildSummaryParts,
  buildExampleSegments,
  exampleWithEquals,
  isSettingDisabled,
  selectedSettingValue,
  selectExamples,
  isLivePreviewSupported,
  buildLiveExampleStrings,
  buildWrittenAddSubMulTex,
  buildWrittenDivTex,
  buildWrittenExampleTex,
} from './presetDetail.js';

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

test('dependent choice settings can be disabled and resolve a forced display value', () => {
  const setting = {
    id: 'questionOrder',
    disabledWhen: (state) => state.dan === 'mixed',
    resolveValue: (state) => (state.dan === 'mixed' ? 'random' : state.questionOrder),
  };

  assert.equal(isSettingDisabled(setting, { dan: 'mixed', questionOrder: 'ascending' }), true);
  assert.equal(selectedSettingValue(setting, { dan: 'mixed', questionOrder: 'ascending' }), 'random');
  assert.equal(isSettingDisabled(setting, { dan: '1', questionOrder: 'ascending' }), false);
  assert.equal(selectedSettingValue(setting, { dan: '1', questionOrder: 'ascending' }), 'ascending');
});

test('buildExampleSegments merges a plain fraction expression into one math segment', () => {
  assert.deepEqual(buildExampleSegments('2/3+3/5'), [
    { type: 'math', latex: '\\frac{2}{3}+\\frac{3}{5}' },
  ]);
});

test('buildExampleSegments converts a mixed number to an integer-plus-frac LaTeX token', () => {
  assert.deepEqual(buildExampleSegments('1 2/3+2 3/5'), [
    { type: 'math', latex: '1\\frac{2}{3}+2\\frac{3}{5}' },
  ]);
});

test('buildExampleSegments converts × and ÷ to LaTeX operators for decimal arithmetic', () => {
  assert.deepEqual(buildExampleSegments('3.6×2.5+4.8÷1.2'), [
    { type: 'math', latex: '3.6\\times2.5+4.8\\div1.2' },
  ]);
});

test('buildExampleSegments keeps Japanese text out of the math segment', () => {
  assert.deepEqual(buildExampleSegments('37 → 奇数'), [
    { type: 'math', latex: '37' },
    { type: 'text', value: ' → 奇数' },
  ]);
});

test('buildExampleSegments splits an arrow-separated fraction conversion into two math segments', () => {
  assert.deepEqual(buildExampleSegments('18/24 → 3/4'), [
    { type: 'math', latex: '\\frac{18}{24}' },
    { type: 'text', value: ' → ' },
    { type: 'math', latex: '\\frac{3}{4}' },
  ]);
});

test('buildExampleSegments handles a Japanese particle and label interleaved with numbers', () => {
  assert.deepEqual(buildExampleSegments('18と24 → 最大公約数6'), [
    { type: 'math', latex: '18' },
    { type: 'text', value: 'と' },
    { type: 'math', latex: '24' },
    { type: 'text', value: ' → 最大公約数' },
    { type: 'math', latex: '6' },
  ]);
});

test('buildExampleSegments merges a trailing = into the preceding math expression', () => {
  assert.deepEqual(buildExampleSegments('2/3+3/5='), [
    { type: 'math', latex: '\\frac{2}{3}+\\frac{3}{5}=' },
  ]);
});

test('exampleWithEquals appends = to a plain arithmetic example', () => {
  assert.equal(exampleWithEquals('2/3+3/5'), '2/3+3/5=');
  assert.equal(exampleWithEquals('1 2/3+2 3/5'), '1 2/3+2 3/5=');
});

test('exampleWithEquals leaves an arrow-based (already-shows-a-result) example untouched', () => {
  assert.equal(exampleWithEquals('18/24 → 3/4'), '18/24 → 3/4');
  assert.equal(exampleWithEquals('37 → 奇数'), '37 → 奇数');
});

test('selectExamples falls back to the static examples when the item has no examplesFor', () => {
  const item = { examples: ['3+5', '6+4'] };
  assert.deepEqual(selectExamples(item, {}), ['3+5', '6+4']);
});

test('selectExamples delegates to examplesFor(settingsState) when present', () => {
  const item = {
    examples: ['34+5', '7+26', '42+35'],
    examplesFor: (settingsState) => (settingsState.carryMode === 'required' ? ['7+26', '48+37'] : ['34+5', '42+35']),
  };
  assert.deepEqual(selectExamples(item, { carryMode: 'required' }), ['7+26', '48+37']);
  assert.deepEqual(selectExamples(item, { carryMode: 'none' }), ['34+5', '42+35']);
});

// isLivePreviewSupported mirrors backend/problem_generation.py's own
// command_type/UNSUPPORTED_OPE_VARIANT_FLAGS check (issue #139).
test('isLivePreviewSupported accepts a plain ope request', () => {
  assert.equal(isLivePreviewSupported({ command_type: 'ope', operator: ['add'] }), true);
});

test('isLivePreviewSupported rejects every non-ope command_type', () => {
  for (const commandType of ['frac', 'mixed', 'gcd', 'lcm', 'divisors', 'multiples', 'evenodd', 'divfrac', 'frac2dec', 'dec2frac', 'squ', 'aBc', '99', 'commondenom', 'simplify']) {
    assert.equal(isLivePreviewSupported({ command_type: commandType }), false, commandType);
  }
});

test('isLivePreviewSupported rejects every unsupported ope variant flag', () => {
  for (const flag of ['use_parentheses', 'missing_value', 'terms', 'terms_min', 'terms_max', 'mixed_operators']) {
    assert.equal(isLivePreviewSupported({ command_type: 'ope', [flag]: true }), false, flag);
  }
});

test('isLivePreviewSupported ignores a falsy ope variant flag', () => {
  assert.equal(isLivePreviewSupported({ command_type: 'ope', use_parentheses: false, terms: 0 }), true);
});

test('isLivePreviewSupported handles a missing command_type without throwing', () => {
  assert.equal(isLivePreviewSupported({}), false);
});

test('buildLiveExampleStrings formats each problem as an unsolved "a<op>b" example', () => {
  const problems = [
    { a: 3, operator: 'add', b: 5 },
    { a: 10, operator: 'sub', b: 6 },
    { a: 2, operator: 'mul', b: 4 },
    { a: 9, operator: 'div', b: 3 },
  ];
  assert.deepEqual(buildLiveExampleStrings(problems), ['3+5', '10-6', '2×4', '9÷3']);
});

test('buildLiveExampleStrings inserts the decimal point from a_decimal_places/b_decimal_places instead of showing the raw scaled integer', () => {
  const problems = [
    { a: 2, operator: 'add', b: 4, a_decimal_places: 1, b_decimal_places: 1 },
    { a: 374, operator: 'sub', b: 28, a_decimal_places: 2, b_decimal_places: 1 },
    { a: 36, operator: 'mul', b: 7, a_decimal_places: 1, b_decimal_places: 0 },
  ];
  assert.deepEqual(buildLiveExampleStrings(problems), ['0.2+0.4', '3.74-2.8', '3.6×7']);
});

test('buildLiveExampleStrings treats a missing a_decimal_places/b_decimal_places as 0 (plain integer)', () => {
  assert.deepEqual(buildLiveExampleStrings([{ a: 3, operator: 'add', b: 5 }]), ['3+5']);
});

test('buildWrittenAddSubMulTex builds a single right-aligned column for plain-integer operands', () => {
  assert.equal(
    buildWrittenAddSubMulTex('34+5'),
    '\\begin{array}{r} 34 \\\\ +5 \\\\ \\hline \\end{array}',
  );
  assert.equal(
    buildWrittenAddSubMulTex('38×7'),
    '\\begin{array}{r} 38 \\\\ \\times7 \\\\ \\hline \\end{array}',
  );
});

test('buildWrittenAddSubMulTex right-aligns decimal operands as plain strings (no separate "." column)', () => {
  // Right-aligning the plain "2.4"/"+3.1" strings lines up the decimal
  // points as a side effect, since add/sub always has equal
  // a_decimal_places/b_decimal_places (drillPresets.js) -- a dedicated "."
  // column was tried and rejected for looking like a disconnected symbol
  // (KaTeX's array has no `@{...}` custom column separator to close the gap).
  assert.equal(
    buildWrittenAddSubMulTex('2.4+3.1'),
    '\\begin{array}{r} 2.4 \\\\ +3.1 \\\\ \\hline \\end{array}',
  );
});

test('buildWrittenAddSubMulTex right-aligns a decimal x integer example on its trailing digit', () => {
  // mul's written convention aligns operands on the trailing (ones) digit,
  // not the decimal point -- exactly what right-alignment already does.
  assert.equal(
    buildWrittenAddSubMulTex('3.6×7'),
    '\\begin{array}{r} 3.6 \\\\ \\times7 \\\\ \\hline \\end{array}',
  );
});

test('buildWrittenAddSubMulTex returns null for a shape it does not recognize', () => {
  assert.equal(buildWrittenAddSubMulTex('18/24 → 3/4'), null);
});

test('buildWrittenDivTex builds a divisor-bracket-overlined-dividend mockup', () => {
  assert.equal(buildWrittenDivTex('84÷4'), '4 \\overline{\\big)\\,84}');
  assert.equal(buildWrittenDivTex('8.4÷4'), '4 \\overline{\\big)\\,8.4}');
});

test('buildWrittenDivTex returns null for a non-division example', () => {
  assert.equal(buildWrittenDivTex('34+5'), null);
});

test('buildWrittenExampleTex dispatches to the long-division mockup for ÷ and the array mockup otherwise', () => {
  assert.equal(buildWrittenExampleTex('84÷4'), buildWrittenDivTex('84÷4'));
  assert.equal(buildWrittenExampleTex('34+5'), buildWrittenAddSubMulTex('34+5'));
});
