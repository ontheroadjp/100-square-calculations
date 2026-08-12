import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';

export const NUMBER_TYPES = ['integers', 'decimals', 'fractions', 'mixed'];
export const OPERATION_GROUPS = ['addition-subtraction', 'multiplication-division', 'four-operations', 'comparison', 'number-sense'];
export const DRILL_FORMS = ['written', 'parentheses', 'missing-value', 'number-sense', 'exam-prep'];

const SPECIAL_TWO_TERM_FLAGS = [
  'intermediate',
  'missing_value',
  'use_parentheses',
  'a_decimal_places',
  'b_decimal_places',
  'mixed_operators',
];

function hasOwn(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function isTwoTermArithmeticPreset(preset) {
  const { params } = preset;
  return params.command_type === 'ope'
    && params.terms === undefined
    && !params.operator.includes('mix')
    && !SPECIAL_TWO_TERM_FLAGS.some((flag) => hasOwn(params, flag));
}

function formatSignature(preset) {
  const params = { ...preset.params };
  delete params.vertical;
  return JSON.stringify(Object.keys(params).sort().map((key) => [key, params[key]]));
}

function getNumberType(preset, bucket) {
  const { params } = preset;
  if (bucket === 'examPrep') return 'integers';
  if (params.command_type === 'mixed') return 'mixed';
  if (params.command_type === 'frac' || params.command_type === 'compare') return 'fractions';
  if (hasOwn(params, 'a_decimal_places') || hasOwn(params, 'b_decimal_places')) return 'decimals';
  return 'integers';
}

function getOperationGroup(preset) {
  const { params } = preset;
  if (params.command_type === 'compare') return 'comparison';
  if (params.command_type === 'com' || ['100', '99', 'aBc', 'squ', 'pi'].includes(params.command_type)) return 'number-sense';
  if (params.operator?.includes('mix')) return 'four-operations';
  if (params.operator?.every((operator) => ['add', 'sub'].includes(operator))) return 'addition-subtraction';
  return 'multiplication-division';
}

function getForms(presets, bucket) {
  const forms = new Set();
  if (bucket === 'examPrep') forms.add('exam-prep');

  for (const preset of Object.values(presets)) {
    if (preset.params.vertical) forms.add('written');
    if (preset.params.use_parentheses) forms.add('parentheses');
    if (preset.params.missing_value) forms.add('missing-value');
    if (getOperationGroup(preset) === 'number-sense') forms.add('number-sense');
  }

  return [...forms];
}

function getLevel(preset, bucket) {
  if (bucket === 'examPrep') return 'exam-prep';
  if (preset.id.includes('advanced') || preset.id.includes('intermediate') || preset.id.includes('-mix') || preset.params.use_parentheses || preset.params.missing_value) return 'advanced';
  if (preset.id.includes('no-carry') || preset.id.includes('complement') || preset.id.includes('hyakumasu') || preset.id.includes('kuku') || preset.id.includes('simple')) return 'basic';
  return 'standard';
}

function canUsePreset(preset, renderer) {
  return (!preset.latexOnly && !preset.params.vertical) || renderer === 'latex';
}

function createCatalogEntries(grade, renderer) {
  const buckets = presetsByGrade[grade];
  const normal = buckets.normal.filter((preset) => canUsePreset(preset, renderer));
  const written = buckets.written.filter((preset) => canUsePreset(preset, renderer));
  const writtenBySignature = new Map(
    written.filter(isTwoTermArithmeticPreset).map((preset) => [formatSignature(preset), preset]),
  );
  const pairedWrittenIds = new Set();

  const entries = normal.map((preset) => {
    const writtenPreset = isTwoTermArithmeticPreset(preset)
      ? writtenBySignature.get(formatSignature(preset))
      : undefined;
    if (writtenPreset) pairedWrittenIds.add(writtenPreset.id);
    const presets = {
      horizontal: preset,
      ...(writtenPreset && { vertical: writtenPreset }),
    };
    return {
      id: preset.id,
      grade,
      numberType: getNumberType(preset, 'normal'),
      operationGroup: getOperationGroup(preset),
      forms: getForms(presets, 'normal'),
      level: getLevel(preset, 'normal'),
      titleKey: preset.catalogTitleKey ?? preset.titleKey,
      descKey: preset.catalogDescKey ?? preset.descKey,
      presets,
    };
  });

  for (const preset of written) {
    if (pairedWrittenIds.has(preset.id)) continue;
    const presets = { vertical: preset };
    entries.push({
      id: preset.id,
      grade,
      numberType: getNumberType(preset, 'written'),
      operationGroup: getOperationGroup(preset),
      forms: getForms(presets, 'written'),
      level: getLevel(preset, 'written'),
      titleKey: preset.catalogTitleKey ?? preset.titleKey,
      descKey: preset.catalogDescKey ?? preset.descKey,
      presets,
    });
  }

  for (const preset of buckets.examPrep.filter((candidate) => canUsePreset(candidate, renderer))) {
    const presets = { horizontal: preset };
    entries.push({
      id: preset.id,
      grade,
      numberType: getNumberType(preset, 'examPrep'),
      operationGroup: getOperationGroup(preset),
      forms: getForms(presets, 'examPrep'),
      level: getLevel(preset, 'examPrep'),
      titleKey: preset.titleKey,
      descKey: preset.descKey,
      presets,
    });
  }

  return entries;
}

export function buildDrillCatalog(renderer = 'reportlab') {
  return [...GRADES, UNGRADED].flatMap((grade) => createCatalogEntries(grade, renderer));
}

export function filterDrillCatalog(catalog, { numberType = null, operationGroup = null, forms = [], grade = null, level = null, query = '' }) {
  const normalizedQuery = query.trim().toLocaleLowerCase();
  return catalog.filter((entry) => (
    (!numberType || entry.numberType === numberType)
    && (!operationGroup || entry.operationGroup === operationGroup)
    && forms.every((form) => entry.forms.includes(form))
    && (!grade || entry.grade === grade)
    && (!level || entry.level === level)
    && (!normalizedQuery || entry.searchText.toLocaleLowerCase().includes(normalizedQuery))
  ));
}

export function addSearchText(catalog, translate) {
  return catalog.map((entry) => ({
    ...entry,
    searchText: `${translate(entry.titleKey)} ${translate(entry.descKey)} ${translate(`number_type_${entry.numberType}`)} ${translate(`operation_group_${entry.operationGroup}`)}`,
  }));
}
