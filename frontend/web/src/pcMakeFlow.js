import { t } from './strings.js';
import { GRADES, presetsByGrade } from './drillPresets.js';
import { PROBLEM_COUNT_OPTIONS, layoutForProblemCount } from './presetDetail.js';
import { getVerticalRows, isVerticalOperation, VERTICAL_COLUMNS } from './verticalLayout.js';
import { ICONS } from './icons.js';

const API_BASE = 'http://127.0.0.1:5000';

// Mirrors catalog.js's CATEGORY_ORDER (docs/uiux/calculation_drill_menu_parameters_v1.md).
// Duplicated rather than imported: catalog.js consumes presetsByGrade for a
// single always-navigating page, while this module needs the same grouping
// driven by in-place state instead of a URL, per issue #101's "own dedicated
// layout/interaction pass" requirement.
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

const DEFAULT_PROBLEM_COUNT = 20;

function canUseItem(item, renderer) {
  return !item.latexOnly || renderer === 'latex';
}

// Matches catalog.js/presetDetail.js's formatExample (docs/uiux/wireframe_v1.png convention).
function formatExample(example) {
  return example.replace(/([+\-×÷])/g, ' $1 ').replace(/\s+/g, ' ').trim();
}

function defaultSettingsState(settings) {
  const state = {};
  for (const setting of settings) {
    if (setting.type === 'choice') state[setting.id] = setting.default;
  }
  return state;
}

function findItemById(grade, id) {
  const categories = presetsByGrade[grade];
  for (const category of Object.keys(categories)) {
    const found = categories[category].find((candidate) => candidate.id === id);
    if (found) return found;
  }
  return null;
}

const buildFileName = (grade, item) => `drill_grade${grade}_${item.id}.pdf`;

export function mountPcMakeFlow(container) {
  const state = {
    activeRenderer: 'reportlab',
    grade: null,
    item: null,
    problemCount: DEFAULT_PROBLEM_COUNT,
    settingsState: {},
    paperSize: 'A4',
    pageCount: 1,
    advancedOpen: false,
    withName: false,
    status: 'idle', // idle | loading | ready | error
    pdfUrl: null,
    error: null,
  };

  function resetDrillState(item) {
    state.problemCount = DEFAULT_PROBLEM_COUNT;
    state.settingsState = item ? defaultSettingsState(item.settings) : {};
    state.paperSize = 'A4';
    state.pageCount = 1;
    state.advancedOpen = false;
    state.withName = false;
    state.status = 'idle';
    if (state.pdfUrl) URL.revokeObjectURL(state.pdfUrl);
    state.pdfUrl = null;
    state.error = null;
  }

  function selectGrade(grade) {
    if (state.grade === grade) return;
    state.grade = grade;
    state.item = null;
    resetDrillState(null);
    renderAll();
  }

  function selectItem(item) {
    state.item = item;
    resetDrillState(item);
    renderAll();
  }

  function gradeColumnHtml() {
    return `
      <ul class="pc-grade-list">
        ${GRADES.map((grade) => `
          <li>
            <button type="button" class="pc-grade-list-item ${state.grade === grade ? 'is-selected' : ''}" data-action="select-grade" data-grade="${grade}">
              ${t(`grade_full_${grade}`)}
            </button>
          </li>
        `).join('')}
      </ul>
    `;
  }

  function pcDrillCardHtml(item) {
    const badgeClass = DIFFICULTY_BADGE_CLASS[item.difficultyKey] ?? 'badge-standard';
    const example = item.examples[0];
    const selected = state.item?.id === item.id;
    return `
      <button type="button" class="drill-list-card pc-drill-list-card ${selected ? 'is-selected' : ''}" data-action="select-item" data-item-id="${item.id}">
        <div class="drill-list-card-heading">
          <h4 class="drill-list-card-title">${t(item.titleKey)}</h4>
          <span class="drill-badge ${badgeClass}">${t(item.difficultyKey)}</span>
        </div>
        ${example ? `<p class="drill-list-card-example">${t('example_prefix')}${formatExample(example)}</p>` : ''}
      </button>
    `;
  }

  function categoryColumnHtml() {
    if (state.grade === null) return `<p class="pc-column-placeholder">${t('pc_select_grade_prompt')}</p>`;

    const categories = presetsByGrade[state.grade];
    const sections = CATEGORY_ORDER
      .filter((category) => categories[category])
      .map((category) => ({
        category,
        items: categories[category].filter((item) => canUseItem(item, state.activeRenderer)),
      }))
      .filter(({ items }) => items.length > 0);

    if (sections.length === 0) return `<p class="drill-empty-state">${t('no_drills_found')}</p>`;

    return sections.map(({ category, items }) => `
      <section class="category-section pc-category-section">
        <h3 class="category-heading">${t(`category_${category}`)}</h3>
        <div class="drill-list">${items.map((item) => pcDrillCardHtml(item)).join('')}</div>
      </section>
    `).join('');
  }

  function renderSettingControl(setting) {
    if (setting.type === 'fixed') {
      return `
        <div class="setting-block">
          <span class="setting-label">${t(setting.labelKey)}</span>
          <span class="setting-fixed-value">${t(setting.valueLabelKey)}</span>
        </div>
      `;
    }
    const showMixedHint = state.settingsState[setting.id] === 'mixed';
    return `
      <div class="setting-block">
        <span class="setting-label">${t(setting.labelKey)}</span>
        <div class="segmented-control" data-role="setting" data-setting-id="${setting.id}">
          ${setting.options.map((option) => `
            <button type="button" class="segmented-option ${state.settingsState[setting.id] === option.value ? 'is-selected' : ''}" data-value="${option.value}">${t(option.labelKey)}</button>
          `).join('')}
        </div>
        ${showMixedHint ? `<p class="setting-hint">${t('setting_mixed_hint')}</p>` : ''}
      </div>
    `;
  }

  function settingsColumnHtml() {
    if (state.grade === null) return `<p class="pc-column-placeholder">${t('pc_select_grade_prompt')}</p>`;
    if (state.item === null) return `<p class="pc-column-placeholder">${t('pc_select_drill_prompt')}</p>`;

    const item = state.item;
    return `
      <div class="preset-detail preset-detail-settings pc-settings-panel">
        <h3 class="preset-detail-title">${t(item.titleKey)}</h3>

        ${item.examples.length > 0 ? `
          <div class="example-chip-row">
            ${item.examples.map((example) => `<span class="example-chip">${formatExample(example)}</span>`).join('')}
          </div>
        ` : ''}

        ${item.supportLevel === 'partial' ? `<p class="support-level-note">${t('support_level_partial_note')}</p>` : ''}
        ${state.status === 'error' ? `<p class="preset-card-error">${t('error_prefix')} ${state.error}</p>` : ''}

        <div class="setting-block">
          <span class="setting-label">${t('problem_count_label')}</span>
          <div class="segmented-control" data-role="problem-count">
            ${PROBLEM_COUNT_OPTIONS.map((count) => `
              <button type="button" class="segmented-option ${state.problemCount === count ? 'is-selected' : ''}" data-value="${count}">${count}${t('problem_count_unit')}</button>
            `).join('')}
          </div>
        </div>

        ${item.settings.map((setting) => renderSettingControl(setting)).join('')}

        <div class="disclosure">
          <button type="button" class="disclosure-toggle" data-action="toggle-advanced" aria-expanded="${state.advancedOpen}">
            <span>${t('advanced_settings_label')}</span>
            <span class="disclosure-chevron ${state.advancedOpen ? 'is-open' : ''}">${ICONS.chevronRight}</span>
          </button>
          ${state.advancedOpen ? `
            <div class="disclosure-body">
              <div class="form-group">
                <label for="pcDetailPaperSize">${t('paper_size')}</label>
                <select id="pcDetailPaperSize" data-role="paper-size">
                  <option value="A4" ${state.paperSize === 'A4' ? 'selected' : ''}>${t('paper_size_a4')}</option>
                  <option value="A3" ${state.paperSize === 'A3' ? 'selected' : ''}>${t('paper_size_a3')}</option>
                  <option value="B5" ${state.paperSize === 'B5' ? 'selected' : ''}>${t('paper_size_b5')}</option>
                  <option value="a4l" ${state.paperSize === 'a4l' ? 'selected' : ''}>${t('paper_size_a4l')}</option>
                </select>
              </div>
              <div class="form-group">
                <label for="pcDetailPageCount">${t('number_of_pages')}</label>
                <input id="pcDetailPageCount" type="number" data-role="page-count" min="1" max="10" value="${state.pageCount}">
              </div>
            </div>
          ` : ''}
        </div>

        <div class="toggle-row">
          <span class="toggle-label">${t('name_field_toggle_label')}</span>
          <button type="button" class="toggle-switch ${state.withName ? 'is-on' : ''}" data-action="toggle-with-name" role="switch" aria-checked="${state.withName}">
            <span class="toggle-switch-thumb"></span>
          </button>
        </div>

        ${item.supportLevel === 'none' ? `<p class="support-level-note">${t('support_level_none_note')}</p>` : ''}

        <button type="button" class="create-pdf-button" data-action="create"
          ${state.status === 'loading' || item.supportLevel === 'none' ? 'disabled' : ''}>
          ${state.status === 'loading' ? t('generating') : (item.supportLevel === 'none' ? t('support_level_none_button') : t('create_pdf_button'))}
        </button>
      </div>
    `;
  }

  function previewColumnHtml() {
    if (state.status === 'loading') return `<p class="pc-column-placeholder">${t('generating')}</p>`;
    if (state.pdfUrl) {
      return `
        <div class="pdf-iframe-container pc-preview-iframe-container">
          <iframe src="${state.pdfUrl}#navpanes=0" class="pdf-iframe" title="pdf-preview"></iframe>
        </div>
        <a href="${state.pdfUrl}" download="${buildFileName(state.grade, state.item)}" class="completion-secondary-button">${t('action_download_pdf')}</a>
      `;
    }
    return `<p class="pc-column-placeholder">${t('pc_preview_placeholder')}</p>`;
  }

  function renderAll() {
    container.innerHTML = `
      <div class="pc-make-flow">
        <div class="pc-flow-topbar">
          <p class="pc-flow-breadcrumb">
            ${t('nav_create')}${state.grade !== null ? ` <span class="pc-flow-breadcrumb-separator">›</span> ${t(`grade_full_${state.grade}`)}` : ''}
          </p>
          <div class="pc-flow-topbar-actions"></div>
        </div>
        <div class="pc-flow-columns">
          <section class="pc-flow-column pc-flow-column-grade">
            <h2 class="pc-column-heading">${t('pc_grade_column_heading')}</h2>
            ${gradeColumnHtml()}
          </section>
          <section class="pc-flow-column pc-flow-column-category">
            <h2 class="pc-column-heading">${t('pc_category_column_heading')}</h2>
            ${categoryColumnHtml()}
          </section>
          <section class="pc-flow-column pc-flow-column-settings">
            <h2 class="pc-column-heading">${t('pc_settings_column_heading')}</h2>
            ${settingsColumnHtml()}
          </section>
          <section class="pc-flow-column pc-flow-column-preview">
            <h2 class="pc-column-heading">${t('preview_heading')}</h2>
            ${previewColumnHtml()}
          </section>
        </div>
      </div>
    `;
  }

  async function generatePdf() {
    if (!state.item) return;
    state.status = 'loading';
    state.error = null;
    renderAll();

    const params = state.item.buildParams(state.settingsState);
    const layout = isVerticalOperation(params)
      ? { rows: getVerticalRows(state.paperSize), columns: VERTICAL_COLUMNS }
      : layoutForProblemCount(state.problemCount);

    const requestBody = {
      paper_size: state.paperSize,
      rows: layout.rows,
      columns: layout.columns,
      page: state.pageCount,
      ...params,
    };

    try {
      const response = await fetch(`${API_BASE}/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error ?? 'PDF generation failed');
      }

      const blob = await response.blob();
      if (state.pdfUrl) URL.revokeObjectURL(state.pdfUrl);
      state.pdfUrl = URL.createObjectURL(blob);
      state.status = 'ready';
    } catch (err) {
      state.error = err.message;
      state.status = 'error';
    }
    renderAll();
  }

  container.addEventListener('click', (event) => {
    const gradeBtn = event.target.closest('[data-action="select-grade"]');
    if (gradeBtn) { selectGrade(Number(gradeBtn.dataset.grade)); return; }

    const itemBtn = event.target.closest('[data-action="select-item"]');
    if (itemBtn) {
      const found = findItemById(state.grade, itemBtn.dataset.itemId);
      if (found) selectItem(found);
      return;
    }

    const actionEl = event.target.closest('[data-action]');
    if (actionEl) {
      const action = actionEl.dataset.action;
      if (action === 'toggle-advanced') { state.advancedOpen = !state.advancedOpen; renderAll(); return; }
      if (action === 'toggle-with-name') { state.withName = !state.withName; renderAll(); return; }
      if (action === 'create') { generatePdf(); return; }
      return;
    }

    const optionEl = event.target.closest('[data-value]');
    if (!optionEl) return;
    const controlEl = optionEl.closest('[data-role]');
    if (!controlEl) return;
    if (controlEl.dataset.role === 'problem-count') {
      state.problemCount = Number(optionEl.dataset.value);
      renderAll();
    } else if (controlEl.dataset.role === 'setting') {
      state.settingsState[controlEl.dataset.settingId] = optionEl.dataset.value;
      renderAll();
    }
  });

  container.addEventListener('input', (event) => {
    if (event.target.dataset.role === 'page-count') {
      state.pageCount = parseInt(event.target.value, 10);
      renderAll();
    }
  });

  container.addEventListener('change', (event) => {
    if (event.target.dataset.role === 'paper-size') {
      state.paperSize = event.target.value;
      renderAll();
    }
  });

  renderAll();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/renderer-info`);
      state.activeRenderer = (await response.json()).renderer;
    } catch {
      // Renderer-info is unreachable (e.g. backend not running yet); the
      // reportlab default keeps latexOnly items hidden, matching catalog.js.
      state.activeRenderer = 'reportlab';
    }
    renderAll();
  })();
}
