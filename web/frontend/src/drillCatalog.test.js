import assert from 'node:assert/strict';
import test from 'node:test';

import { addSearchText, buildDrillCatalog, DRILL_FORMS, filterDrillCatalog, NUMBER_TYPES } from './drillCatalog.js';

test('latex catalog merges every eligible two-term arithmetic format pair', () => {
  const catalog = buildDrillCatalog('latex');
  const paired = catalog.filter((entry) => Object.keys(entry.presets).length === 2);

  assert.ok(paired.length > 0);
  for (const entry of paired) {
    assert.ok(entry.presets.horizontal, entry.id);
    assert.ok(entry.presets.vertical, entry.id);
    assert.equal(entry.presets.horizontal.params.vertical, undefined, entry.id);
    assert.equal(entry.presets.vertical.params.vertical, true, entry.id);
  }

  const unpairedEligible = catalog.filter((entry) => (
    entry.presets.horizontal
    && entry.presets.horizontal.params.command_type === 'ope'
    && entry.presets.horizontal.params.terms === undefined
    && !entry.presets.horizontal.params.operator.includes('mix')
    && !entry.presets.horizontal.params.intermediate
    && !entry.presets.horizontal.params.missing_value
    && !entry.presets.horizontal.params.use_parentheses
    && entry.presets.horizontal.params.a_decimal_places === undefined
    && entry.presets.horizontal.params.b_decimal_places === undefined
    && !entry.presets.vertical
  ));
  assert.deepEqual(unpairedEligible, []);
});

test('reportlab catalog omits written-format choices without hiding compatible drills', () => {
  const catalog = buildDrillCatalog('reportlab');
  const gradeTwoAddition = catalog.find((entry) => entry.id === 'g2-add2');

  assert.ok(gradeTwoAddition);
  assert.deepEqual(Object.keys(gradeTwoAddition.presets), ['horizontal']);
});

test('catalog supports number type, operation group, format, grade, level, and translated-text filters', () => {
  const catalog = addSearchText(buildDrillCatalog('latex'), (key) => key);
  const fractionDrills = filterDrillCatalog(catalog, { numberType: 'fractions', grade: 4 });
  const advancedDrills = filterDrillCatalog(catalog, { level: 'advanced' });
  const searchedDrills = filterDrillCatalog(catalog, { query: 'preset_g4_fraction_title' });
  const parenthesizedMissingValueDrills = filterDrillCatalog(catalog, {
    numberType: 'integers',
    operationGroup: 'four-operations',
    forms: ['parentheses', 'missing-value'],
  });

  assert.ok(fractionDrills.length > 0);
  assert.ok(fractionDrills.every((entry) => entry.numberType === 'fractions' && entry.grade === 4));
  assert.ok(advancedDrills.every((entry) => entry.level === 'advanced'));
  assert.ok(searchedDrills.length > 0);
  assert.ok(parenthesizedMissingValueDrills.length === 0);
  assert.deepEqual(NUMBER_TYPES, ['integers', 'decimals', 'fractions', 'mixed']);
  assert.deepEqual(DRILL_FORMS, ['written', 'parentheses', 'missing-value', 'number-sense', 'exam-prep']);
});

test('integer format filters can be combined when matching presets are added', () => {
  const catalog = [{
    id: 'combined-format',
    numberType: 'integers',
    operationGroup: 'addition-subtraction',
    forms: ['parentheses', 'missing-value'],
    grade: 4,
    level: 'advanced',
    searchText: '',
  }];

  assert.deepEqual(filterDrillCatalog(catalog, {
    numberType: 'integers',
    operationGroup: 'addition-subtraction',
    forms: ['parentheses', 'missing-value'],
  }), catalog);
});
