import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';

export const NUMBER_TYPES = ['integers', 'decimals', 'fractions', 'mixed'];
export const OPERATION_GROUPS = ['addition-subtraction', 'multiplication-division', 'four-operations', 'comparison', 'number-sense'];
// The written(筆算)/missing-value(虫食い算) format distinctions from before
// #98 have no equivalent in docs/uiux/calculation_drill_menu_parameters_v1.md
// and were dropped from the data model (see issue #111); no format-level
// filter remains today.
export const DRILL_FORMS = [];

const NUMBER_SENSE_COMMANDS = [
  'com', '99', '100', 'squ', 'pi', 'aBc',
  'evenodd', 'multiples', 'divisors', 'lcm', 'gcd',
  'simplify', 'commondenom', 'frac2dec', 'dec2frac', 'divfrac',
];

const FRACTION_COMMANDS = ['frac', 'simplify', 'commondenom', 'frac2dec', 'dec2frac', 'divfrac'];

const LEVEL_BY_DIFFICULTY_KEY = {
  difficulty_basic: 'basic',
  difficulty_standard: 'standard',
  difficulty_basic_standard: 'standard',
};

function defaultSettingsState(settings) {
  const state = {};
  for (const setting of settings) {
    if (setting.type === 'choice') state[setting.id] = setting.default;
  }
  return state;
}

// Mirrors the pre-#98 classification (params-driven, not category-driven)
// so catalog.js's hardcoded NUMBER_TYPE_GROUPS keep working unchanged.
function getOperationGroup(params) {
  if (params.command_type === 'compare') return 'comparison';
  if (NUMBER_SENSE_COMMANDS.includes(params.command_type)) return 'number-sense';
  const operators = params.operator ?? [];
  if (params.mixed_operators || operators.includes('mix')) return 'four-operations';
  if (operators.length > 0 && operators.every((operator) => ['add', 'sub'].includes(operator))) return 'addition-subtraction';
  return 'multiplication-division';
}

function getNumberType(params) {
  if (params.command_type === 'mixed') return 'mixed';
  if (FRACTION_COMMANDS.includes(params.command_type)) return 'fractions';
  if (params.a_decimal_places || params.b_decimal_places || params.decimal_places) return 'decimals';
  return 'integers';
}

function getLevel(item) {
  return LEVEL_BY_DIFFICULTY_KEY[item.difficultyKey] ?? 'standard';
}

function canUseItem(item, renderer) {
  return !item.latexOnly || renderer === 'latex';
}

function createCatalogEntries(grade, renderer) {
  const categories = presetsByGrade[grade];
  const entries = [];
  for (const items of Object.values(categories)) {
    for (const item of items) {
      if (!canUseItem(item, renderer)) continue;
      const params = item.buildParams(defaultSettingsState(item.settings));
      entries.push({
        id: item.id,
        grade,
        numberType: getNumberType(params),
        operationGroup: getOperationGroup(params),
        forms: [],
        level: getLevel(item),
        titleKey: item.titleKey,
        descKey: item.descKey,
        supportLevel: item.supportLevel,
        presets: { default: { titleKey: item.titleKey, descKey: item.descKey, params } },
      });
    }
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
