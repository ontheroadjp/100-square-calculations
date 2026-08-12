import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getVerticalRows,
  isVerticalOperation,
  VERTICAL_COLUMNS,
} from './verticalLayout.js';

test('uses paper-specific row counts for vertical worksheets', () => {
  assert.equal(getVerticalRows('A3'), 4);
  assert.equal(getVerticalRows('A4'), 4);
  assert.equal(getVerticalRows('B5'), 2);
  assert.equal(getVerticalRows('a4l'), 2);
  assert.equal(VERTICAL_COLUMNS, 2);
});

test('recognizes only vertical operation requests', () => {
  assert.equal(isVerticalOperation({ command_type: 'ope', vertical: true }), true);
  assert.equal(isVerticalOperation({ command_type: 'ope', vertical: false }), false);
  assert.equal(isVerticalOperation({ command_type: '99', vertical: true }), false);
});
