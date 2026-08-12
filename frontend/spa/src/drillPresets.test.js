import assert from 'node:assert/strict';
import test from 'node:test';

import { presetsByGrade } from './drillPresets.js';
import ja from '../public/locales/ja/translation.json' with { type: 'json' };
import en from '../public/locales/en/translation.json' with { type: 'json' };

const EXAM_PREP_GRADES = [4, 5, 6];
const EXPECTED_STAGES = ['basic', 'intermediate', 'advanced'];
const EXPECTED_LEVELS = ['1', '2', '3'];
const EXPECTED_TERMS_BY_LEVEL = { 1: 3, 2: 4, 3: 5 };

test('non-exam-prep grades have an empty examPrep bucket', () => {
  for (const grade of [1, 2, 3]) {
    assert.deepEqual(presetsByGrade[grade].examPrep, []);
  }
});

test('grade 1 has six carry and borrowing addition/subtraction presets', () => {
  const expected = [
    ['g1-add-no-carry', ['add'], 'none', 1, 9],
    ['g1-add-carry', ['add'], 'required', 1, 9],
    ['g1-sub-no-borrow', ['sub'], 'none', 1, 9],
    ['g1-sub-borrow', ['sub'], 'required', 10, 19],
    ['g1-addsub-no-carry', ['add', 'sub'], 'none', 1, 9],
    ['g1-addsub-all', ['add', 'sub'], 'mixed', 1, 9],
  ];

  const gradeOnePresets = presetsByGrade[1].normal;
  for (const [id, operators, carryMode, aMin, aMax] of expected) {
    const preset = gradeOnePresets.find((candidate) => candidate.id === id);
    assert.ok(preset, `missing ${id}`);
    assert.equal(preset.latexOnly, true, `${id} must be latexOnly`);
    assert.deepEqual(preset.params.operator, operators, id);
    assert.equal(preset.params.carry_mode, carryMode, id);
    assert.equal(preset.params.a_min, aMin, id);
    assert.equal(preset.params.a_max, aMax, id);
    assert.equal(preset.params.b_min, 1, id);
    assert.equal(preset.params.b_max, 9, id);
  }

  assert.ok(!gradeOnePresets.some((preset) => ['g1-add', 'g1-sub', 'g1-addsub'].includes(preset.id)));
});

test('each exam-prep grade has exactly 9 latexOnly presets covering every stage/level', () => {
  for (const grade of EXAM_PREP_GRADES) {
    const presets = presetsByGrade[grade].examPrep;
    assert.equal(presets.length, 9);

    const ids = presets.map((preset) => preset.id);
    assert.equal(new Set(ids).size, 9, `duplicate ids for grade ${grade}`);

    for (const stage of EXPECTED_STAGES) {
      for (const level of EXPECTED_LEVELS) {
        const id = `g${grade}-examprep-${stage}-${level}`;
        assert.ok(ids.includes(id), `missing ${id}`);
      }
    }

    for (const preset of presets) {
      assert.equal(preset.latexOnly, true, `${preset.id} must be latexOnly`);
      assert.equal(preset.params.command_type, 'ope');
      assert.deepEqual(preset.params.operator, ['mix']);
      assert.equal(preset.params.b_value, 1);
    }
  }
});

test('term count increases with level and matches the simulated design', () => {
  for (const grade of EXAM_PREP_GRADES) {
    for (const preset of presetsByGrade[grade].examPrep) {
      const level = preset.id.slice(-1);
      assert.equal(preset.params.terms, EXPECTED_TERMS_BY_LEVEL[level], preset.id);
    }
  }
});

test('use_parentheses and mixed_operators are only set (and true) for the intended stages', () => {
  for (const grade of EXAM_PREP_GRADES) {
    for (const preset of presetsByGrade[grade].examPrep) {
      const isBasic = preset.id.includes('-basic-');
      const isAdvanced = preset.id.includes('-advanced-');

      if (isBasic) {
        assert.equal(preset.params.mixed_operators, undefined, preset.id);
      } else {
        assert.equal(preset.params.mixed_operators, true, preset.id);
      }

      if (isAdvanced) {
        assert.equal(preset.params.use_parentheses, true, preset.id);
      } else {
        assert.equal(preset.params.use_parentheses, undefined, preset.id);
      }
    }
  }
});

test('first-operand digit range (a_value) increases by grade, matching the simulated design', () => {
  const expectedAValue = { 4: 1, 5: 2, 6: 3 };
  for (const grade of EXAM_PREP_GRADES) {
    for (const preset of presetsByGrade[grade].examPrep) {
      assert.equal(preset.params.a_value, expectedAValue[grade], preset.id);
    }
  }
});

const DECIMAL_PRESET_IDS_BY_GRADE = {
  3: ['g3-decimal-addsub'],
  4: ['g4-decimal-addsub', 'g4-decimal-mul', 'g4-decimal-div'],
  5: ['g5-decimal-mul', 'g5-decimal-div'],
};

test('decimal presets exist for grades 3-5, are latexOnly, and target the ope command', () => {
  for (const [grade, expectedIds] of Object.entries(DECIMAL_PRESET_IDS_BY_GRADE)) {
    const ids = presetsByGrade[grade].normal.map((preset) => preset.id);
    for (const id of expectedIds) {
      assert.ok(ids.includes(id), `missing ${id}`);
    }
    for (const preset of presetsByGrade[grade].normal) {
      if (!expectedIds.includes(preset.id)) continue;
      assert.equal(preset.latexOnly, true, preset.id);
      assert.equal(preset.params.command_type, 'ope', preset.id);
      assert.ok(
        preset.params.a_decimal_places > 0 || preset.params.b_decimal_places > 0,
        `${preset.id} must set at least one decimal-places param`,
      );
    }
  }
});

test('decimal mul/div presets with an integer second operand omit b_decimal_places', () => {
  for (const id of ['g4-decimal-mul', 'g4-decimal-div']) {
    const preset = presetsByGrade[4].normal.find((candidate) => candidate.id === id);
    assert.equal(preset.params.b_decimal_places, undefined, id);
  }
});

test('grade-6 mixed presets exist, are latexOnly, and target the mixed command', () => {
  const ids = presetsByGrade[6].normal.map((preset) => preset.id);
  assert.ok(ids.includes('g6-mixed-basic'));
  assert.ok(ids.includes('g6-mixed-advanced'));

  const basic = presetsByGrade[6].normal.find((preset) => preset.id === 'g6-mixed-basic');
  const advanced = presetsByGrade[6].normal.find((preset) => preset.id === 'g6-mixed-advanced');

  for (const preset of [basic, advanced]) {
    assert.equal(preset.latexOnly, true, preset.id);
    assert.equal(preset.params.command_type, 'mixed', preset.id);
    assert.deepEqual(preset.params.a_kind, ['int', 'decimal', 'fraction'], preset.id);
    assert.deepEqual(preset.params.b_kind, ['int', 'decimal', 'fraction'], preset.id);
  }

  assert.equal(basic.params.terms, 2);
  assert.equal(basic.params.mixed_operators, undefined);
  assert.equal(advanced.params.terms, 3);
  assert.equal(advanced.params.mixed_operators, true);
});

test('fraction comparison presets cover the requested grade and pattern matrix', () => {
  const expected = {
    4: [
      ['g4-fraction-compare-same-denominator', 'same-denominator', false],
      ['g4-fraction-compare-same-numerator', 'same-numerator', false],
      ['g4-fraction-compare-same-denominator-advanced', 'same-denominator', true],
      ['g4-fraction-compare-same-numerator-advanced', 'same-numerator', true],
    ],
    5: [
      ['g5-fraction-compare-different-denominators', 'different-denominators', false],
      ['g5-fraction-compare-different-denominators-advanced', 'different-denominators', true],
    ],
  };

  for (const [grade, cards] of Object.entries(expected)) {
    for (const [id, pattern, advanced] of cards) {
      const preset = presetsByGrade[grade].normal.find((candidate) => candidate.id === id);
      assert.ok(preset, `missing ${id}`);
      assert.equal(preset.latexOnly, true, id);
      assert.equal(preset.params.command_type, 'compare', id);
      assert.equal(preset.params.comparison_pattern, pattern, id);
      assert.ok(ja[preset.titleKey], `missing Japanese title translation for ${id}`);
      assert.ok(ja[preset.descKey], `missing Japanese description translation for ${id}`);
      assert.ok(en[preset.titleKey], `missing English title translation for ${id}`);
      assert.ok(en[preset.descKey], `missing English description translation for ${id}`);
      if (advanced) {
        assert.equal(preset.params.a_fraction_form, 'mix', id);
        assert.equal(preset.params.b_fraction_form, 'mix', id);
      }
    }
  }
});

test('grades 1-2 and ungraded have no decimal or mixed presets', () => {
  for (const grade of [1, 2]) {
    const ids = presetsByGrade[grade].normal.map((preset) => preset.id);
    assert.ok(!ids.some((id) => id.includes('decimal') || id.includes('mixed')));
  }
});
