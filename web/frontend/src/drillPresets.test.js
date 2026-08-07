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
