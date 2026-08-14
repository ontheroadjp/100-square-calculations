import katex from 'katex';
import { t } from './strings.js';
import { getVerticalRows, isVerticalOperation, VERTICAL_COLUMNS } from './verticalLayout.js';
import { ICONS } from './icons.js';

const API_BASE = 'http://127.0.0.1:5000';

export const PROBLEM_COUNT_OPTIONS = [10, 20, 30];
const DEFAULT_PROBLEM_COUNT = 20;

// Maps the problem-count choice to nuts_calc.py's rows/columns. 20 matches
// the previous hardcoded default (10 rows x 2 columns).
const LAYOUT_BY_PROBLEM_COUNT = {
  10: { rows: 5, columns: 2 },
  20: { rows: 10, columns: 2 },
  30: { rows: 10, columns: 3 },
};

export function layoutForProblemCount(problemCount) {
  return LAYOUT_BY_PROBLEM_COUNT[problemCount] ?? LAYOUT_BY_PROBLEM_COUNT[DEFAULT_PROBLEM_COUNT];
}

function defaultSettingsState(settings) {
  const state = {};
  for (const setting of settings) {
    if (setting.type === 'choice') state[setting.id] = setting.default;
  }
  return state;
}

// Matches, in priority order, the arithmetic tokens worth typesetting as
// LaTeX: a mixed number ("1 2/3"), a plain fraction ("2/3"), a decimal
// ("3.6"), a bare integer, or an operator/paren. Anything not matched here
// (arrows, commas, Japanese words like "奇数"/"最大公約数", "…", the "と"
// particle) is left as plain text -- KaTeX's own font has no CJK glyphs, so
// non-arithmetic text must never be handed to it.
const MATH_TOKEN_RE = /(\d+\s+\d+\/\d+)|(\d+\/\d+)|(\d+\.\d+)|(\d+)|([+\-×÷=()])/g;

function tokenToLatex(token) {
  const mixed = token.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixed) return `${mixed[1]}\\frac{${mixed[2]}}{${mixed[3]}}`;
  const fraction = token.match(/^(\d+)\/(\d+)$/);
  if (fraction) return `\\frac{${fraction[1]}}{${fraction[2]}}`;
  if (token === '×') return '\\times';
  if (token === '÷') return '\\div';
  return token;
}

// Splits an example string into text/math segments so the caller can render
// each math run through KaTeX while leaving text runs as plain text.
// Adjacent math tokens (e.g. the "2/3" and "+" and "3/5" in "2/3+3/5") are
// merged into a single LaTeX expression so KaTeX applies normal operator
// spacing; a gap of any other character flushes the current expression.
export function buildExampleSegments(example) {
  const segments = [];
  let mathLatex = '';
  let lastIndex = 0;

  const flushMath = () => {
    if (mathLatex) {
      segments.push({ type: 'math', latex: mathLatex });
      mathLatex = '';
    }
  };

  for (const match of example.matchAll(MATH_TOKEN_RE)) {
    const gap = example.slice(lastIndex, match.index);
    if (gap) {
      flushMath();
      segments.push({ type: 'text', value: gap });
    }
    mathLatex += tokenToLatex(match[0]);
    lastIndex = match.index + match[0].length;
  }
  flushMath();

  const tail = example.slice(lastIndex);
  if (tail) segments.push({ type: 'text', value: tail });

  return segments;
}

// Appends "=" to a plain arithmetic example ("2/3+3/5" -> "2/3+3/5=") so it
// reads as an unsolved problem. Examples that already show a result via "→"
// (frac2dec/simplify/evenodd/etc.) are left untouched -- appending "=" to
// "18/24 → 3/4" would not make sense.
export function exampleWithEquals(example) {
  return example.includes('→') ? example : `${example}=`;
}

const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const escapeHtml = (str) => str.replace(/[&<>"']/g, (ch) => HTML_ESCAPES[ch]);

function renderExampleHtml(example) {
  return buildExampleSegments(exampleWithEquals(example)).map((segment) => (
    segment.type === 'math'
      ? katex.renderToString(segment.latex, { throwOnError: false })
      : escapeHtml(segment.value)
  )).join('');
}

// Builds the "20問・標準・繰り上がり：まぜる" style summary shown on the
// completion screen. `translate` is injected rather than using the module's
// own `t` import so callers (and tests) can verify the assembled parts
// without depending on strings.ja.json's actual Japanese copy.
export function buildSummaryParts({ problemCount, difficultyKey, settings, settingsState }, translate) {
  const parts = [`${problemCount}${translate('problem_count_unit')}`, translate(difficultyKey)];
  for (const setting of settings) {
    if (setting.type === 'choice') {
      const option = setting.options.find((candidate) => candidate.value === settingsState[setting.id]);
      if (option) parts.push(`${translate(setting.labelKey)}：${translate(option.labelKey)}`);
    } else {
      parts.push(`${translate(setting.labelKey)}：${translate(setting.valueLabelKey)}`);
    }
  }
  return parts;
}

const buildFileName = (grade, item) => `drill_grade${grade}_${item.id}.pdf`;

export function mountPresetDetail(container, { grade, item, onBack }) {
  container.classList.add(`grade-${grade}`);

  const state = {
    screen: 'settings', // settings | done | preview
    problemCount: DEFAULT_PROBLEM_COUNT,
    settingsState: defaultSettingsState(item.settings),
    paperSize: 'A4',
    pageCount: 1,
    advancedOpen: false,
    withName: false,
    status: 'idle', // idle | loading | ready | error
    pdfUrl: null,
    error: null,
  };

  function renderSettingControl(setting) {
    if (setting.type === 'fixed') {
      return `
        <div class="setting-block">
          <span class="setting-label">${t(setting.labelKey)}</span>
          <span class="setting-fixed-value">${t(setting.valueLabelKey)}</span>
        </div>
      `;
    }
    const selectedOption = setting.options.find((option) => option.value === state.settingsState[setting.id]);
    return `
      <div class="setting-block">
        <span class="setting-label">${t(setting.labelKey)}</span>
        <div class="segmented-control" data-role="setting" data-setting-id="${setting.id}">
          ${setting.options.map((option) => `
            <button type="button" class="segmented-option ${state.settingsState[setting.id] === option.value ? 'is-selected' : ''}" data-value="${option.value}">${t(option.labelKey)}</button>
          `).join('')}
        </div>
        ${selectedOption?.hintKey ? `<p class="setting-hint">${t(selectedOption.hintKey)}</p>` : ''}
      </div>
    `;
  }

  function renderSettingsScreen() {
    return `
      <div class="preset-detail preset-detail-settings">
        <header class="catalog-header">
            <div class="catalog-header-title">
                <a class="page-header-row" href="index.html">
                    ${ICONS.chevronLeft}
                    <h1 class="catalog-heading">${t(item.titleKey)}(${t(`grade_full_${grade}`)})</h1>
                </a>
            </div>
            <p class="category-picker-heading catalog-header-sub-title">${t('category_picker_heading')}</p>
        </header>


        <div class="page-header-row" data-action="back">
            <h3 class="preset-detail-title">問題サンプル</h3>
        </div>

        ${item.examples.length > 0 ? `
          <div class="example-chip-row">
            ${item.examples.map((example) => `<span class="example-chip">${renderExampleHtml(example)}</span>`).join('')}
          </div>
        ` : ''}

        ${item.supportLevel === 'partial' ? `<p class="support-level-note">${t('support_level_partial_note')}</p>` : ''}
        ${state.status === 'error' ? `<p class="preset-card-error">${t('error_prefix')} ${state.error}</p>` : ''}

        <div class="specific-setting-block">
            ${item.settings.map((setting) => renderSettingControl(setting)).join('')}
        </div>

        <div class="disclosure">
          <button type="button" class="disclosure-toggle" data-action="toggle-advanced" aria-expanded="${state.advancedOpen}">
            <span>${t('advanced_settings_label')}</span>
            <span class="disclosure-chevron ${state.advancedOpen ? 'is-open' : ''}">${ICONS.chevronRight}</span>
          </button>
          ${state.advancedOpen ? `
            <div class="disclosure-body">
              <div class="setting-block">
                <h3 class="setting-label">${t('problem_count_label')}</h3>
                <div class="segmented-control" data-role="problem-count">
                  ${PROBLEM_COUNT_OPTIONS.map((count) => `
                  <button type="button" class="segmented-option ${state.problemCount === count ? 'is-selected' : ''}" data-value="${count}">${count}${t('problem_count_unit')}</button>
                  `).join('')}
                </div>
              </div>
              <div class="form-group">
                <label for="detailPaperSize">${t('paper_size')}</label>
                <select id="detailPaperSize" data-role="paper-size">
                  <option value="A4" ${state.paperSize === 'A4' ? 'selected' : ''}>${t('paper_size_a4')}</option>
                  <option value="A3" ${state.paperSize === 'A3' ? 'selected' : ''}>${t('paper_size_a3')}</option>
                  <option value="B5" ${state.paperSize === 'B5' ? 'selected' : ''}>${t('paper_size_b5')}</option>
                  <option value="a4l" ${state.paperSize === 'a4l' ? 'selected' : ''}>${t('paper_size_a4l')}</option>
                </select>
              </div>
              <div class="form-group">
                <label for="detailPageCount">${t('number_of_pages')}</label>
                <input id="detailPageCount" type="number" data-role="page-count" min="1" max="10" value="${state.pageCount}">
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

  function renderDoneScreen() {
    const summary = buildSummaryParts(
      { problemCount: state.problemCount, difficultyKey: item.difficultyKey, settings: item.settings, settingsState: state.settingsState },
      t,
    );
    return `
      <div class="preset-detail preset-detail-done">
        <div class="completion-visual">
          <span class="confetti-dot confetti-dot-1"></span>
          <span class="confetti-dot confetti-dot-2"></span>
          <span class="confetti-dot confetti-dot-3"></span>
          <span class="confetti-dot confetti-dot-4"></span>
          <span class="confetti-dot confetti-dot-5"></span>
          <span class="confetti-dot confetti-dot-6"></span>
          <span class="completion-check" aria-hidden="true">${ICONS.checkDone}</span>
        </div>
        <h3 class="completion-heading">${t('completion_heading')}</h3>
        <p class="completion-summary">
          ${t(`grade_full_${grade}`)}<br>
          ${t(item.titleKey)}<br>
          ${summary.join('・')}
        </p>

        <div class="completion-thumbnail" aria-hidden="true"></div>

        <div class="completion-actions">
          <button type="button" class="create-pdf-button" data-action="open-preview">${t('action_open_pdf')}</button>
          <a href="${state.pdfUrl}" download="${buildFileName(grade, item)}" class="completion-secondary-button">${t('action_download_pdf')}</a>
          <button type="button" class="completion-secondary-button" data-action="regenerate" ${state.status === 'loading' ? 'disabled' : ''}>${t('action_same_condition')}</button>
          <a href="index.html" class="completion-secondary-button">${t('action_back_to_top')}</a>
        </div>
      </div>
    `;
  }

  function renderPreviewScreen() {
    return `
      <div class="preset-detail preset-detail-preview">
        <header class="preview-header">
          <button type="button" class="page-header-row" data-action="back-to-done">${ICONS.chevronLeft}<h3 class="preset-detail-title">${t('preview_heading')}</h3></button>
        </header>
        <div class="pdf-iframe-container preview-iframe-container">
          <iframe src="${state.pdfUrl}#navpanes=0" class="pdf-iframe" title="pdf-preview"></iframe>
        </div>
      </div>
    `;
  }

  function render() {
    if (state.screen === 'done') {
      container.innerHTML = renderDoneScreen();
    } else if (state.screen === 'preview') {
      container.innerHTML = renderPreviewScreen();
    } else {
      container.innerHTML = renderSettingsScreen();
    }
  }

  async function generatePdf() {
    state.status = 'loading';
    state.error = null;
    render();

    const params = item.buildParams(state.settingsState);
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
      state.screen = 'done';
    } catch (err) {
      state.error = err.message;
      state.status = 'error';
      state.screen = 'settings';
    }
    render();
  }

  container.addEventListener('click', (event) => {
    const actionEl = event.target.closest('[data-action]');
    if (actionEl) {
      const action = actionEl.dataset.action;
      if (action === 'back') { onBack(); return; }
      if (action === 'toggle-advanced') { state.advancedOpen = !state.advancedOpen; render(); return; }
      if (action === 'toggle-with-name') { state.withName = !state.withName; render(); return; }
      if (action === 'create' || action === 'regenerate') { generatePdf(); return; }
      if (action === 'open-preview') { state.screen = 'preview'; render(); return; }
      if (action === 'back-to-done') { state.screen = 'done'; render(); return; }
      return;
    }

    const optionEl = event.target.closest('[data-value]');
    if (!optionEl) return;
    const controlEl = optionEl.closest('[data-role]');
    if (!controlEl) return;
    if (controlEl.dataset.role === 'problem-count') {
      state.problemCount = Number(optionEl.dataset.value);
      render();
    } else if (controlEl.dataset.role === 'setting') {
      state.settingsState[controlEl.dataset.settingId] = optionEl.dataset.value;
      render();
    }
  });

  container.addEventListener('input', (event) => {
    if (event.target.dataset.role === 'page-count') {
      state.pageCount = parseInt(event.target.value, 10);
      render();
    }
  });

  container.addEventListener('change', (event) => {
    if (event.target.dataset.role === 'paper-size') {
      state.paperSize = event.target.value;
      render();
    }
  });

  render();
}
