import { test } from 'node:test';
import assert from 'node:assert/strict';
import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';

const KNOWN_CATEGORIES = new Set([
  'addition', 'subtraction', 'multiplication', 'division',
  'fraction', 'four-operations', 'number-sense',
]);

const KNOWN_SUPPORT_LEVELS = new Set(['full', 'partial', 'none']);

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
    assert.equal(typeof item.difficultyKey, 'string', `${context}: difficultyKey must be a string`);
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
      } else if (setting.type === 'fixed') {
        assert.equal(typeof setting.valueLabelKey, 'string', `${context}: fixed setting must have valueLabelKey`);
      } else {
        assert.fail(`${context}: unknown setting type "${setting.type}"`);
      }
    }
  }
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
