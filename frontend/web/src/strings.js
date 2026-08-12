import ja from './strings.ja.json';

export function t(key) {
  return ja[key] ?? key;
}
