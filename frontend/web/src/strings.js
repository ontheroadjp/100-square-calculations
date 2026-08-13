import ja from './strings.ja.json' with { type: 'json' };

export function t(key) {
  return ja[key] ?? key;
}
