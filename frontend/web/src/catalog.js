import './styles/main.scss';
import { t } from './strings.js';
import { GRADES, presetsByGrade } from './drillPresets.js';
import { mountNavShell } from './navShell.js';
import { ICONS } from './icons.js';

mountNavShell();

const API_BASE = 'http://127.0.0.1:5000';

// Matches the doc's たし算/ひき算/かけ算/わり算/... ordering
// (docs/uiux/calculation_drill_menu_parameters_v1.md). Object key order in
// drillPresets.js's presetsByGrade varies per grade (e.g. grade4 lists
// division before addition), so section order is driven by this fixed list
// rather than Object.keys() insertion order.
const CATEGORY_ORDER = [
  'addition', 'subtraction', 'multiplication', 'division',
  'fraction', 'four-operations', 'number-sense',
];

const DIFFICULTY_BADGE_CLASS = {
  difficulty_basic: 'badge-basic',
  difficulty_standard: 'badge-standard',
  difficulty_basic_standard: 'badge-standard',
  difficulty_advanced: 'badge-advanced',
};

function canUseItem(item, renderer) {
  return !item.latexOnly || renderer === 'latex';
}

// Renders examples ("625+75") with spaces around the operator for
// readability, matching docs/uiux/wireframe_v1.png ("625 + 75"). Arrows in
// number-sense examples ("37 → 奇数") already carry their own spacing.
function formatExample(example) {
  return example.replace(/([+\-×÷])/g, ' $1 ').replace(/\s+/g, ' ').trim();
}

function drillCardHtml(grade, item) {
  const badgeClass = DIFFICULTY_BADGE_CLASS[item.difficultyKey] ?? 'badge-standard';
  const example = item.examples[0];
  return `
    <a class="drill-list-card" href="preset.html?grade=${grade}&drillId=${encodeURIComponent(item.id)}&format=default">
      <div class="drill-list-card-heading">
        <h3 class="drill-list-card-title">${t(item.titleKey)}</h3>
        <span class="drill-badge ${badgeClass}">${t(item.difficultyKey)}</span>
      </div>
      ${example ? `<p class="drill-list-card-example">${t('example_prefix')}${formatExample(example)}</p>` : ''}
    </a>
  `;
}

function categorySectionHtml(grade, category, items) {
  return `
    <section class="category-section">
      <h2 class="category-heading">${t(`category_${category}`)}</h2>
      <div class="drill-list">${items.map((item) => drillCardHtml(grade, item)).join('')}</div>
    </section>
  `;
}

function emptyStateHtml() {
  return `
    <p class="drill-empty-state">${t('no_drills_found')}</p>
    <a class="back-button" href="index.html">${ICONS.back}<span>${t('back')}</span></a>
  `;
}

async function render() {
  const params = new URLSearchParams(location.search);
  const gradeParam = Number(params.get('grade'));
  const grade = GRADES.includes(gradeParam) ? gradeParam : null;
  const container = document.getElementById('catalog');

  if (grade === null) {
    container.innerHTML = emptyStateHtml();
    return;
  }

  container.classList.add(`grade-${grade}`);

  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    activeRenderer = (await response.json()).renderer;
  } catch {
    activeRenderer = 'reportlab';
  }

  const categories = presetsByGrade[grade];
  const sections = CATEGORY_ORDER
    .filter((category) => categories[category])
    .map((category) => ({
      category,
      items: categories[category].filter((item) => canUseItem(item, activeRenderer)),
    }))
    .filter(({ items }) => items.length > 0);

  container.innerHTML = `
    <header class="catalog-header">
        <div class="catalog-header-title">
            <a class="page-header-row" href="index.html">${ICONS.chevronLeft}<h1 class="catalog-heading">${t(`grade_full_${grade}`)}</h1></a>
        </div>
        <p class="category-picker-heading catalog-header-sub-title">${t('category_picker_heading')}</p>
    </header>
    ${sections.length > 0
      ? sections.map(({ category, items }) => categorySectionHtml(grade, category, items)).join('')
      : emptyStateHtml()}
  `;
}

render();
