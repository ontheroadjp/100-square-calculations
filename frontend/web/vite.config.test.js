import assert from 'node:assert/strict';
import test from 'node:test';

import config from './vite.config.js';

test('enables CSS source maps for development', () => {
  assert.equal(config.css.devSourcemap, true);
  assert.equal(config.build.sourcemap, undefined);
});
