import './styles/main.scss';
import { t } from './strings.js';
import { UNGRADED } from './drillPresets.js';
import { buildDrillCatalog, filterDrillCatalog } from './drillCatalog.js';
import { mountNavShell } from './navShell.js';

mountNavShell();

const API_BASE = 'http://127.0.0.1:5000';
const NUMBER_TYPE_GROUPS = {
  integers: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  decimals: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  fractions: ['addition-subtraction', 'multiplication-division', 'comparison'],
};
const INTEGER_FORMAT_FILTERS = ['parentheses', 'missing-value'];

function parseGrade(raw) {
  if (!raw) return null;
  return raw === UNGRADED ? UNGRADED : Number(raw);
}

function catalogHref({ numberType = null, grade = null, level = null, forms = [] } = {}) {
  const params = new URLSearchParams();
  if (numberType) params.set('numberType', numberType);
  if (grade !== null && grade !== undefined) params.set('grade', grade);
  if (level) params.set('level', level);
  forms.forEach((form) => params.append('forms', form));
  const query = params.toString();
  return query ? `catalog.html?${query}` : 'catalog.html';
}

function drillCardHtml(drill, { inNumberTypeView, numberType, forms, level }) {
  const formats = Object.entries(drill.presets);
  const gradeHref = catalogHref(inNumberTypeView
    ? { numberType, forms, grade: drill.grade, level }
    : { grade: drill.grade, level });
  const levelHref = catalogHref(inNumberTypeView
    ? { numberType, forms, grade: drill.grade, level: drill.level }
    : { grade: drill.grade, level: drill.level });

  return `
    <article class="preset-card">
      <div class="drill-badges">
        <a class="drill-badge grade-badge" href="${gradeHref}">${t(`grade_${drill.grade}`)}</a>
        <a class="drill-badge level-badge" href="${levelHref}">${t(`level_${drill.level}`)}</a>
      </div>
      <h3 class="preset-card-title">${t(drill.titleKey)}</h3>
      <p class="preset-card-desc">${t(drill.descKey)}</p>
      <div class="drill-card-actions">
        ${formats.map(([format]) => `
          <a class="preset-download-button" href="preset.html?grade=${drill.grade}&drillId=${encodeURIComponent(drill.id)}&format=${format}">
            ${formats.length > 1 ? t(`format_${format}`) : t('generate_pdf')}
          </a>
        `).join('')}
      </div>
    </article>
  `;
}

function drillGridHtml(drills, context) {
  if (drills.length === 0) return `<p class="drill-empty-state">${t('no_drills_found')}</p>`;
  return `<div class="preset-card-grid">${drills.map((drill) => drillCardHtml(drill, context)).join('')}</div>`;
}

function numberTypeCatalogHtml(catalog, numberType, context) {
  const groups = NUMBER_TYPE_GROUPS[numberType];
  const groupsHtml = groups
    ? groups.map((group) => {
      const drills = catalog.filter((drill) => drill.operationGroup === group);
      if (drills.length === 0) return '';
      return `
        <section class="number-type-section">
          <h2>${t(`operation_group_${group}`)}</h2>
          <p>${t(`operation_group_${group}_desc`)}</p>
          ${drillGridHtml(drills, context)}
        </section>
      `;
    }).join('')
    : drillGridHtml(catalog, context);

  return `
    <header class="number-type-header">
      <h1>${t(`number_type_${numberType}`)}</h1>
      <p>${t(`number_type_${numberType}_intro`)}</p>
    </header>
    ${groupsHtml}
  `;
}

async function render() {
  const params = new URLSearchParams(location.search);
  const numberType = params.get('numberType') || null;
  const grade = parseGrade(params.get('grade'));
  const level = params.get('level') || null;
  const forms = params.getAll('forms');

  document.querySelector('[name="numberType"]').value = numberType ?? '';
  document.querySelector('[name="grade"]').value = grade ?? '';
  document.querySelector('[name="level"]').value = level ?? '';

  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    activeRenderer = (await response.json()).renderer;
  } catch {
    activeRenderer = 'reportlab';
  }

  const catalog = buildDrillCatalog(activeRenderer).filter((drill) => drill.grade !== UNGRADED);
  const filteredDrills = filterDrillCatalog(catalog, { numberType, forms, grade, level });
  const availableNumberTypeDrills = filterDrillCatalog(catalog, { numberType, grade, level });
  const inNumberTypeView = Boolean(numberType);
  const context = { inNumberTypeView, numberType, forms, level };

  const formatFilterFieldset = document.getElementById('formatFilter');
  if (inNumberTypeView && numberType === 'integers') {
    const availableForms = INTEGER_FORMAT_FILTERS.filter((form) => availableNumberTypeDrills.some((drill) => drill.forms.includes(form)));
    if (availableForms.length > 0) {
      document.getElementById('formatFilterOptions').innerHTML = availableForms.map((form) => `
        <label>
          <input type="checkbox" name="forms" value="${form}" ${forms.includes(form) ? 'checked' : ''}>
          ${t(`form_${form}`)}
        </label>
      `).join('');
      formatFilterFieldset.hidden = false;
    } else {
      formatFilterFieldset.hidden = true;
    }
  } else {
    formatFilterFieldset.hidden = true;
  }

  const results = document.getElementById('results');
  results.innerHTML = inNumberTypeView
    ? numberTypeCatalogHtml(filteredDrills, numberType, context)
    : drillGridHtml(filteredDrills, context);
}

render();
