import assert from 'node:assert/strict';
import test from 'node:test';

import { presetsByGrade } from './drillPresets.js';

const EXAM_PREP_GRADES = [4, 5, 6];
const EXPECTED_STAGES = ['basic', 'intermediate', 'advanced'];
const EXPECTED_LEVELS = ['1', '2', '3'];
const EXPECTED_TERMS_BY_LEVEL = { 1: 3, 2: 4, 3: 5 };

test('non-exam-prep grades have an empty examPrep bucket', () => {
  for (const grade of [1, 2, 3]) {
    assert.deepEqual(presetsByGrade[grade].examPrep, []);
  }
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

test('grades 1-2 and ungraded have no decimal or mixed presets', () => {
  for (const grade of [1, 2]) {
    const ids = presetsByGrade[grade].normal.map((preset) => preset.id);
    assert.ok(!ids.some((id) => id.includes('decimal') || id.includes('mixed')));
  }
});
