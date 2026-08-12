import { t } from './strings.js';
import { GRADES, UNGRADED, CUSTOM_GRADE } from './drillPresets.js';
import {
  addSearchText,
  buildDrillCatalog,
  DRILL_FORMS,
  filterDrillCatalog,
  NUMBER_TYPES,
} from './drillCatalog.js';
import { mountPresetDetail } from './presetDetail.js';
import { mountCustomGenerator } from './customGenerator.js';

const API_BASE = 'http://127.0.0.1:5000';

const NUMBER_TYPE_GROUPS = {
  integers: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  decimals: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  fractions: ['addition-subtraction', 'multiplication-division', 'comparison'],
};
const INTEGER_FORMAT_FILTERS = ['parentheses', 'missing-value'];

function escapeAttr(value) {
  return String(value).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

function drillCardHtml(drill) {
  const formats = Object.entries(drill.presets);
  return `
    <article class="preset-card">
      <div class="drill-badges">
        <button type="button" class="drill-badge grade-badge" data-action="select-grade" data-grade="${drill.grade}">${t(`grade_${drill.grade}`)}</button>
        <button type="button" class="drill-badge level-badge" data-action="select-level" data-level="${drill.level}">${t(`level_${drill.level}`)}</button>
      </div>
      <h3 class="preset-card-title">${t(drill.titleKey)}</h3>
      <p class="preset-card-desc">${t(drill.descKey)}</p>
      <div class="drill-card-actions">
        ${formats.map(([format]) => `
          <button type="button" class="preset-download-button" data-action="open-preset" data-drill-id="${drill.id}" data-format="${format}">
            ${formats.length > 1 ? t(`format_${format}`) : t('generate_pdf')}
          </button>
        `).join('')}
      </div>
    </article>
  `;
}

function drillGridHtml(drills) {
  if (drills.length === 0) return `<p class="drill-empty-state">${t('no_drills_found')}</p>`;
  return `<div class="preset-card-grid">${drills.map(drillCardHtml).join('')}</div>`;
}

function numberTypeCatalogHtml(catalog, availableCatalog, numberType, forms) {
  const groups = NUMBER_TYPE_GROUPS[numberType];
  const availableForms = numberType === 'integers'
    ? INTEGER_FORMAT_FILTERS.filter((form) => availableCatalog.some((drill) => drill.forms.includes(form)))
    : [];

  const groupsHtml = groups
    ? groups.map((group) => {
      const drills = catalog.filter((drill) => drill.operationGroup === group);
      if (drills.length === 0) return '';
      return `
        <section class="number-type-section">
          <h2>${t(`operation_group_${group}`)}</h2>
          <p>${t(`operation_group_${group}_desc`)}</p>
          ${drillGridHtml(drills)}
        </section>
      `;
    }).join('')
    : drillGridHtml(catalog);

  return `
    <header class="number-type-header">
      <h1>${t(`number_type_${numberType}`)}</h1>
      <p>${t(`number_type_${numberType}_intro`)}</p>
    </header>
    ${availableForms.length > 0 ? `
      <fieldset class="format-filter" aria-label="${t('format_filter_label')}">
        <legend>${t('format_filter_label')}</legend>
        ${availableForms.map((form) => `
          <label>
            <input type="checkbox" data-action="toggle-form" data-form="${form}" ${forms.includes(form) ? 'checked' : ''}>
            ${t(`form_${form}`)}
          </label>
        `).join('')}
      </fieldset>
    ` : ''}
    ${groupsHtml}
  `;
}

export function mountGradeDrills(root) {
  const state = {
    route: 'home',
    selectedNumberType: null,
    selectedForms: [],
    selectedGrade: null,
    selectedLevel: null,
    query: '',
    openPreset: null,
    activeRenderer: 'reportlab',
  };

  fetch(`${API_BASE}/renderer-info`)
    .then((response) => response.json())
    .then((data) => { state.activeRenderer = data.renderer; render(); })
    .catch(() => { state.activeRenderer = 'reportlab'; render(); });

  function openCatalog({ numberType = null, forms = [], grade = null, level = null } = {}) {
    state.route = 'catalog';
    state.selectedNumberType = numberType;
    state.selectedForms = forms;
    state.selectedGrade = grade;
    state.selectedLevel = level;
    render();
  }

  function toggleForm(form) {
    state.selectedForms = state.selectedForms.includes(form)
      ? state.selectedForms.filter((candidate) => candidate !== form)
      : [...state.selectedForms, form];
    render();
  }

  function inNumberTypeView() {
    return Boolean(state.selectedNumberType) && !state.query.trim();
  }

  function render() {
    const hadSearchFocus = document.activeElement?.dataset?.role === 'search-input';
    const selectionStart = hadSearchFocus ? document.activeElement.selectionStart : null;

    root.innerHTML = '';
    const view = document.createElement('div');
    view.className = 'grade-drills';
    root.appendChild(view);

    if (state.openPreset) {
      mountPresetDetail(view, {
        grade: state.openPreset.grade,
        preset: state.openPreset.preset,
        onBack: () => { state.openPreset = null; render(); },
      });
      return;
    }

    if (state.route === CUSTOM_GRADE) {
      mountCustomGenerator(view, { supportsVertical: state.activeRenderer === 'latex' });
      return;
    }

    const catalog = addSearchText(buildDrillCatalog(state.activeRenderer), t);
    const filteredDrills = filterDrillCatalog(catalog, {
      numberType: state.selectedNumberType,
      forms: state.selectedForms,
      grade: state.selectedGrade,
      level: state.selectedLevel,
      query: state.query,
    });
    const availableNumberTypeDrills = filterDrillCatalog(catalog, {
      numberType: state.selectedNumberType,
      grade: state.selectedGrade,
      level: state.selectedLevel,
      query: state.query,
    });
    const availableHomeForms = DRILL_FORMS.filter((form) => catalog.some((drill) => drill.forms.includes(form)));
    const showCatalog = state.route === 'catalog' || state.query.trim() !== '';

    view.innerHTML = `
      <div class="drill-search">
        <label for="drillSearch">${t('drill_search_label')}</label>
        <input id="drillSearch" type="search" data-role="search-input" value="${escapeAttr(state.query)}" placeholder="${escapeAttr(t('drill_search_placeholder'))}">
      </div>
      <nav class="grade-nav" aria-label="${t('drill_navigation_label')}">
        <button type="button" data-action="nav-home" class="grade-link ${state.route === 'home' ? 'active' : ''}">${t('nav_home')}</button>
        <button type="button" data-action="nav-custom" class="grade-link ${state.route === CUSTOM_GRADE ? 'active' : ''}">${t('nav_custom')}</button>
      </nav>

      ${showCatalog ? `
        <div class="drill-filter-bar" aria-label="${t('drill_filter_label')}">
          <select aria-label="${t('number_type_filter_label')}" data-role="filter-number-type">
            <option value="">${t('all_number_types')}</option>
            ${NUMBER_TYPES.map((numberType) => `<option value="${numberType}" ${state.selectedNumberType === numberType ? 'selected' : ''}>${t(`number_type_${numberType}`)}</option>`).join('')}
          </select>
          <select aria-label="${t('grade_select_label')}" data-role="filter-grade">
            <option value="">${t('all_grades')}</option>
            ${GRADES.map((grade) => `<option value="${grade}" ${state.selectedGrade === grade ? 'selected' : ''}>${t(`grade_${grade}`)}</option>`).join('')}
            <option value="${UNGRADED}" ${state.selectedGrade === UNGRADED ? 'selected' : ''}>${t(`grade_${UNGRADED}`)}</option>
          </select>
          <select aria-label="${t('level_filter_label')}" data-role="filter-level">
            <option value="">${t('all_levels')}</option>
            ${['basic', 'standard', 'advanced', 'exam-prep'].map((level) => `<option value="${level}" ${state.selectedLevel === level ? 'selected' : ''}>${t(`level_${level}`)}</option>`).join('')}
          </select>
          <button type="button" class="filter-reset" data-action="clear-filters">${t('clear_filters')}</button>
        </div>
        ${state.selectedNumberType && !state.query.trim()
          ? numberTypeCatalogHtml(filteredDrills, availableNumberTypeDrills, state.selectedNumberType, state.selectedForms)
          : drillGridHtml(filteredDrills)}
      ` : `
        <p class="grade-drills-intro">${t('drill_home_intro')}</p>
        <section class="drill-home-section">
          <h2>${t('number_type_start_title')}</h2>
          <div class="drill-start-grid">
            ${NUMBER_TYPES.map((numberType) => `<button type="button" class="drill-start-card" data-action="open-numbertype" data-number-type="${numberType}">${t(`number_type_${numberType}`)}</button>`).join('')}
          </div>
        </section>
        <section class="drill-home-section">
          <h2>${t('form_start_title')}</h2>
          <div class="drill-start-grid">
            ${availableHomeForms.map((form) => `<button type="button" class="drill-start-card" data-action="open-form" data-form="${form}">${t(`form_${form}`)}</button>`).join('')}
          </div>
        </section>
        <section class="drill-home-section">
          <h2>${t('grade_start_title')}</h2>
          <div class="drill-start-grid grade-start-grid">
            ${[...GRADES, UNGRADED].map((grade) => `<button type="button" class="drill-start-card" data-action="open-grade" data-grade="${grade}">${t(`grade_${grade}`)}</button>`).join('')}
          </div>
        </section>
      `}
    `;

    if (hadSearchFocus) {
      const input = view.querySelector('[data-role="search-input"]');
      if (input) {
        input.focus();
        input.setSelectionRange(selectionStart, selectionStart);
      }
    }

    view.addEventListener('input', (event) => {
      if (event.target.dataset.role === 'search-input') {
        state.query = event.target.value;
        openCatalog({});
      }
    });

    view.addEventListener('change', (event) => {
      const role = event.target.dataset.role;
      if (role === 'filter-number-type') {
        state.selectedNumberType = event.target.value || null;
        render();
      } else if (role === 'filter-grade') {
        const value = event.target.value;
        state.selectedGrade = value === '' ? null : (value === UNGRADED ? UNGRADED : Number(value));
        render();
      } else if (role === 'filter-level') {
        state.selectedLevel = event.target.value || null;
        render();
      }
    });

    view.addEventListener('click', (event) => {
      const actionEl = event.target.closest('[data-action]');
      const toggleEl = event.target.closest('[data-action="toggle-form"]');
      if (toggleEl) {
        toggleForm(toggleEl.dataset.form);
        return;
      }
      if (!actionEl) return;
      const { action } = actionEl.dataset;

      if (action === 'nav-home') {
        state.route = 'home';
        state.query = '';
        render();
      } else if (action === 'nav-custom') {
        state.route = CUSTOM_GRADE;
        render();
      } else if (action === 'clear-filters') {
        openCatalog();
      } else if (action === 'open-preset') {
        const drill = catalog.find((candidate) => candidate.id === actionEl.dataset.drillId);
        const preset = drill?.presets[actionEl.dataset.format];
        if (drill && preset) {
          state.openPreset = { grade: drill.grade, preset };
          render();
        }
      } else if (action === 'select-grade') {
        const raw = actionEl.dataset.grade;
        const grade = raw === UNGRADED ? UNGRADED : Number(raw);
        openCatalog(inNumberTypeView()
          ? { numberType: state.selectedNumberType, forms: state.selectedForms, grade, level: state.selectedLevel }
          : { grade, level: state.selectedLevel });
      } else if (action === 'select-level') {
        const level = actionEl.dataset.level;
        openCatalog(inNumberTypeView()
          ? { numberType: state.selectedNumberType, forms: state.selectedForms, grade: state.selectedGrade, level }
          : { grade: state.selectedGrade, level });
      } else if (action === 'open-numbertype') {
        openCatalog({ numberType: actionEl.dataset.numberType });
      } else if (action === 'open-form') {
        openCatalog({ forms: [actionEl.dataset.form] });
      } else if (action === 'open-grade') {
        const raw = actionEl.dataset.grade;
        openCatalog({ grade: raw === UNGRADED ? UNGRADED : Number(raw) });
      }
    });
  }

  render();
}
