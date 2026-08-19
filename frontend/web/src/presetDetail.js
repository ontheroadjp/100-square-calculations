import katex from 'katex';
import { t } from './strings.js';
import { getVerticalRows, isVerticalOperation, VERTICAL_COLUMNS } from './verticalLayout.js';
import { ICONS } from './icons.js';
import { pageHeaderHtml } from './pageHeader.js';

const API_BASE = 'http://127.0.0.1:5000';

export const PROBLEM_COUNT_OPTIONS = [10, 20, 30];
const DEFAULT_PROBLEM_COUNT = 20;

// Mirrors backend/problem_generation.py's UNSUPPORTED_OPE_VARIANT_FLAGS and its
// `command_type != 'ope'` check (backend/problem_generation.py:28-35,58-68):
// POST /generate-problems only supports plain two-term 'ope' arithmetic today.
// Every other command_type (frac/mixed/gcd/... , issue #166's sub-issues) and
// these ope variant flags raise a 500 there, so items using them keep the
// static examples/examplesFor from #135 instead of calling the endpoint.
const UNSUPPORTED_OPE_VARIANT_FLAGS = [
  'use_parentheses', 'missing_value', 'terms', 'terms_min', 'terms_max', 'mixed_operators',
];

const LIVE_EXAMPLE_COUNT = 3; // matches the length of every static `examples` array
const LIVE_EXAMPLE_FETCH_DEBOUNCE_MS = 300;
const OPERATOR_SYMBOLS = { add: '+', sub: '-', mul: '×', div: '÷' };

export function isLivePreviewSupported(params) {
  return params?.command_type === 'ope' && !UNSUPPORTED_OPE_VARIANT_FLAGS.some((flag) => params[flag]);
}

// Mirrors backend/nuts_calc_tex.py's format_decimal_value(raw, places): a/b
// from POST /generate-problems are always the raw (unscaled) integers
// calc_add/calc_sub/calc_mul/calc_div produce, with a_decimal_places/
// b_decimal_places (0 by default) recording where the decimal point
// belongs -- the API response never formats this itself.
function formatDecimalValue(raw, places) {
  if (places <= 0) return String(raw);
  const digits = String(raw).padStart(places + 1, '0');
  return `${digits.slice(0, -places)}.${digits.slice(-places)}`;
}

export function buildLiveExampleStrings(problems) {
  return problems.map((problem) => {
    const aStr = formatDecimalValue(problem.a, problem.a_decimal_places ?? 0);
    const bStr = formatDecimalValue(problem.b, problem.b_decimal_places ?? 0);
    return `${aStr}${OPERATOR_SYMBOLS[problem.operator]}${bStr}`;
  });
}

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

export function selectedSettingValue(setting, settingsState) {
  return setting.resolveValue?.(settingsState) ?? settingsState[setting.id];
}

export function isSettingDisabled(setting, settingsState) {
  return setting.disabledWhen?.(settingsState) ?? false;
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

// Matches the plain two-operand "a<op>b" shape every displayFormat-eligible
// item's examples/examplesFor and live-preview strings (buildLiveExampleStrings)
// use -- the only shape 出題形式:筆算 (issue #134) is offered on.
const WRITTEN_EXAMPLE_RE = /^(\d+(?:\.\d+)?)([+\-×÷])(\d+(?:\.\d+)?)$/;
const WRITTEN_OPERATOR_TEX = { '+': '+', '-': '-', '×': '\\times', '÷': '\\div' };

// Builds a KaTeX `array`-based written-calculation (筆算) mockup for an
// add/sub/mul example: two right-aligned rows (operand a; operator +
// operand b) and a rule below, left unsolved (no answer row) to match the
// horizontal ("式") chips' "a+b=" convention (exampleWithEquals).
//
// A single right-aligned column (not a 3-column int/"."/frac split) is
// correct for every displayFormat-eligible item without extra logic: add/sub
// items always send equal a_decimal_places/b_decimal_places (drillPresets.js
// enforces this, mirroring nuts_calc_tex.py's own validation), so both
// operands' trailing digit is their last fractional digit and right-aligning
// the plain strings lines up the decimal points as a side effect; mul's
// written convention aligns operands on their trailing (ones) digit, not the
// decimal point, which is exactly what right-alignment already does. A
// separate "." column (KaTeX's `array` has no `@{...}` custom separator, so
// that would need its own column) was tried and rejected -- the default
// column gap around an isolated "." makes it read as a disconnected symbol
// rather than part of the number.
export function buildWrittenAddSubMulTex(example) {
  const match = example.match(WRITTEN_EXAMPLE_RE);
  if (!match) return null;
  const [, a, operatorSymbol, b] = match;
  const opTex = WRITTEN_OPERATOR_TEX[operatorSymbol];
  return `\\begin{array}{r} ${a} \\\\ ${opTex}${b} \\\\ \\hline \\end{array}`;
}

// Builds a long-division bracket mockup for a div example. KaTeX has no
// `\enclose{longdiv}` (a MathJax-only extension, unsupported as of KaTeX
// v0.16), so this approximates nuts_calc_tex.py's `longdivision`-package
// vertical rendering with `\overline{\big)...}`: a divisor, a bracket, and
// an overlined dividend.
export function buildWrittenDivTex(example) {
  const match = example.match(WRITTEN_EXAMPLE_RE);
  if (!match || match[2] !== '÷') return null;
  const [, a, , b] = match;
  return `${b} \\overline{\\big)\\,${a}}`;
}

export function buildWrittenExampleTex(example) {
  return example.includes('÷') ? buildWrittenDivTex(example) : buildWrittenAddSubMulTex(example);
}

// Falls back to the horizontal ("式") rendering if an example doesn't match
// the plain "a<op>b" shape (defensive -- every displayFormat-eligible item's
// examples are verified to match, see drillPresets.js).
function renderWrittenExampleHtml(example) {
  const tex = buildWrittenExampleTex(example);
  return tex ? katex.renderToString(tex, { throwOnError: false }) : renderExampleHtml(example);
}

// Builds the "20問・標準・繰り上がり：まぜる" style summary shown on the
// completion screen. `translate` is injected rather than using the module's
// own `t` import so callers (and tests) can verify the assembled parts
// without depending on strings.ja.json's actual Japanese copy.
export function buildSummaryParts({ problemCount, difficultyKey, settings, settingsState }, translate) {
  const parts = [`${problemCount}${translate('problem_count_unit')}`, translate(difficultyKey)];
  for (const setting of settings) {
    if (setting.type === 'choice') {
      const selectedValue = selectedSettingValue(setting, settingsState);
      const option = setting.options.find((candidate) => candidate.value === selectedValue);
      if (option) parts.push(`${translate(setting.labelKey)}：${translate(option.labelKey)}`);
    } else {
      parts.push(`${translate(setting.labelKey)}：${translate(setting.valueLabelKey)}`);
    }
  }
  return parts;
}

const buildFileName = (grade, item) => `drill_grade${grade}_${item.id}.pdf`;

// Picks the example-chip content for the current settings: items whose
// example set changes with the selected choice settings (carryMode,
// remainderMode, denominator, numberKind, reduction, dan) provide
// `examplesFor(settingsState)`; other items keep their static `examples`.
export function selectExamples(item, settingsState) {
  return item.examplesFor ? item.examplesFor(settingsState) : item.examples;
}

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
    liveExamples: null,
    liveExamplesStatus: 'idle', // idle | loading | ready | error
  };

  let liveExampleFetchTimer = null;
  let liveExampleFetchToken = 0;

  async function fetchLiveExamples(params) {
    const token = ++liveExampleFetchToken;
    state.liveExamplesStatus = 'loading';

    try {
      const response = await fetch(`${API_BASE}/generate-problems`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper_size: state.paperSize, num: LIVE_EXAMPLE_COUNT, ...params }),
      });
      if (!response.ok) throw new Error('live example fetch failed');
      const data = await response.json();
      if (token !== liveExampleFetchToken) return; // superseded by a newer settings change
      state.liveExamples = buildLiveExampleStrings(data.problems);
      state.liveExamplesStatus = 'ready';
    } catch {
      if (token !== liveExampleFetchToken) return;
      // Backend unreachable or erroring: fall back to the static examples
      // (selectExamples) instead of surfacing this to the user, since the
      // example chips are a non-critical preview, not the PDF generation path.
      state.liveExamples = null;
      state.liveExamplesStatus = 'error';
    }
    render();
  }

  function scheduleLiveExampleFetch() {
    if (liveExampleFetchTimer) clearTimeout(liveExampleFetchTimer);
    const params = item.buildParams(state.settingsState);
    if (!isLivePreviewSupported(params)) {
      liveExampleFetchToken += 1; // discard any in-flight fetch's result
      state.liveExamples = null;
      state.liveExamplesStatus = 'idle';
      return;
    }
    liveExampleFetchTimer = setTimeout(() => fetchLiveExamples(params), LIVE_EXAMPLE_FETCH_DEBOUNCE_MS);
  }

  function currentExamples() {
    const params = item.buildParams(state.settingsState);
    if (isLivePreviewSupported(params) && state.liveExamples) return state.liveExamples;
    return selectExamples(item, state.settingsState);
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
    const selectedValue = selectedSettingValue(setting, state.settingsState);
    const disabled = isSettingDisabled(setting, state.settingsState);
    const selectedOption = setting.options.find((option) => option.value === selectedValue);
    return `
      <div class="setting-block">
        <span class="setting-label">${t(setting.labelKey)}</span>
        <div class="segmented-control ${disabled ? 'is-disabled' : ''}" data-role="setting" data-setting-id="${setting.id}" aria-disabled="${disabled}">
          ${setting.options.map((option) => `
            <button type="button" class="segmented-option ${selectedValue === option.value ? 'is-selected' : ''}" data-value="${option.value}" ${disabled ? 'disabled' : ''}>${t(option.labelKey)}</button>
          `).join('')}
        </div>
        ${selectedOption?.hintKey ? `<p class="setting-hint">${t(selectedOption.hintKey)}</p>` : ''}
      </div>
    `;
  }

  function renderSettingsScreen() {
    const examples = currentExamples();
    const isWrittenFormat = isVerticalOperation(item.buildParams(state.settingsState));
    return `
      <div class="preset-detail preset-detail-settings">
        ${pageHeaderHtml(`${t(item.titleKey)}(${t(`grade_full_${grade}`)})`, t(item.pointKey))}

        <div class="page-header-row" data-action="back">
            <h3 class="preset-detail-title">問題サンプル</h3>
        </div>

        ${examples.length > 0 ? `
          <div class="example-chip-row">
            ${examples.map((example) => `<span class="example-chip${isWrittenFormat ? ' example-chip-written' : ''}">${isWrittenFormat ? renderWrittenExampleHtml(example) : renderExampleHtml(example)}</span>`).join('')}
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
    if (!optionEl || optionEl.disabled) return;
    const controlEl = optionEl.closest('[data-role]');
    if (!controlEl) return;
    if (controlEl.dataset.role === 'problem-count') {
      state.problemCount = Number(optionEl.dataset.value);
      render();
    } else if (controlEl.dataset.role === 'setting') {
      state.settingsState[controlEl.dataset.settingId] = optionEl.dataset.value;
      scheduleLiveExampleFetch();
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

  scheduleLiveExampleFetch();
  render();
}
