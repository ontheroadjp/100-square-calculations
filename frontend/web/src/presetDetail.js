import { t } from './strings.js';
import { getVerticalRows, isVerticalOperation, VERTICAL_COLUMNS } from './verticalLayout.js';

const API_BASE = 'http://127.0.0.1:5000';

// Maps the simplified "problem density" choice to nuts_calc.py's rows/columns.
// 'standard' matches the previous hardcoded default (10 rows x 2 columns).
const DENSITY_OPTIONS = [
  { value: 'few', labelKey: 'density_few', rows: 5, columns: 2 },
  { value: 'standard', labelKey: 'density_standard', rows: 10, columns: 2 },
  { value: 'many', labelKey: 'density_many', rows: 10, columns: 4 },
];
const DEFAULT_DENSITY = 'standard';

const buildFileName = (grade, preset) => `drill_grade${grade}_${preset.id}.pdf`;

export function mountPresetDetail(container, { grade, preset, onBack }) {
  const isVerticalPreset = isVerticalOperation(preset.params);
  const supportsDensity = preset.params.command_type !== '100' && !isVerticalPreset;

  const state = {
    numberValue: preset.numberInput?.default ?? null,
    paperSize: 'A4',
    pageCount: 1,
    density: DEFAULT_DENSITY,
    status: 'idle', // idle | loading | ready | error
    pdfUrl: null,
    error: null,
    lastGenerated: null,
  };

  const isDirty = () => (
    !state.lastGenerated
    || state.lastGenerated.paperSize !== state.paperSize
    || state.lastGenerated.pageCount !== state.pageCount
    || state.lastGenerated.density !== state.density
    || state.lastGenerated.numberValue !== state.numberValue
  );

  async function generatePdf() {
    const densityOption = DENSITY_OPTIONS.find((option) => option.value === state.density) ?? DENSITY_OPTIONS[1];
    const layout = isVerticalPreset
      ? { rows: getVerticalRows(state.paperSize), columns: VERTICAL_COLUMNS }
      : densityOption;

    state.status = 'loading';
    state.error = null;
    render();

    const requestBody = {
      paper_size: state.paperSize,
      rows: layout.rows,
      columns: layout.columns,
      page: state.pageCount,
      ...preset.params,
      ...(preset.numberInput && { [preset.numberInput.param]: state.numberValue }),
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
      state.pdfUrl = URL.createObjectURL(blob);
      state.status = 'ready';
      state.lastGenerated = {
        paperSize: state.paperSize,
        pageCount: state.pageCount,
        density: state.density,
        numberValue: state.numberValue,
      };
    } catch (err) {
      state.error = err.message;
      state.status = 'error';
    }
    render();
  }

  function render() {
    container.innerHTML = `
      <div class="preset-detail">
        <button type="button" class="back-button" data-action="back">${t('back')}</button>

        <h3 class="preset-detail-title">${t(preset.titleKey)}</h3>

        ${state.status === 'loading' ? `<p class="preset-detail-status">${t('generating')}</p>` : ''}
        ${state.status === 'error' ? `<p class="preset-card-error">${t('error_prefix')} ${state.error}</p>` : ''}
        ${state.pdfUrl ? `
          <div class="pdf-iframe-container">
            <iframe src="${state.pdfUrl}" class="pdf-iframe" title="pdf-preview"></iframe>
          </div>
        ` : ''}

        <div class="preset-detail-settings">
          ${preset.numberInput ? `
            <div class="form-group">
              <label for="detailNumberInput">${t(preset.numberInput.labelKey)}</label>
              <input id="detailNumberInput" type="number" data-role="number-value"
                min="${preset.numberInput.min}" max="${preset.numberInput.max}"
                value="${state.numberValue}">
            </div>
          ` : ''}
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
          ${supportsDensity ? `
            <div class="form-group">
              <label for="detailDensity">${t('problem_density')}</label>
              <select id="detailDensity" data-role="density">
                ${DENSITY_OPTIONS.map((option) => `
                  <option value="${option.value}" ${state.density === option.value ? 'selected' : ''}>${t(option.labelKey)}</option>
                `).join('')}
              </select>
            </div>
          ` : ''}
        </div>

        <div class="preset-detail-actions">
          <button type="button" class="regenerate-button" data-action="regenerate"
            ${state.status === 'loading' || !isDirty() ? 'disabled' : ''}>
            ${state.status === 'loading' ? t('generating') : t('regenerate_pdf')}
          </button>
          ${state.status === 'ready' && state.pdfUrl ? `
            <a href="${state.pdfUrl}" download="${buildFileName(grade, preset)}" class="preset-download-button">${t('download_pdf')}</a>
          ` : `
            <button type="button" class="preset-download-button" disabled>${t('download_pdf')}</button>
          `}
        </div>
      </div>
    `;
  }

  container.addEventListener('click', (event) => {
    const actionEl = event.target.closest('[data-action]');
    if (!actionEl) return;
    if (actionEl.dataset.action === 'back') onBack();
    if (actionEl.dataset.action === 'regenerate') generatePdf();
  });

  container.addEventListener('input', (event) => {
    const role = event.target.dataset.role;
    if (role === 'number-value') {
      state.numberValue = parseInt(event.target.value, 10);
      render();
    } else if (role === 'page-count') {
      state.pageCount = parseInt(event.target.value, 10);
      render();
    }
  });

  container.addEventListener('change', (event) => {
    const role = event.target.dataset.role;
    if (role === 'paper-size') {
      state.paperSize = event.target.value;
      render();
    } else if (role === 'density') {
      state.density = event.target.value;
      render();
    }
  });

  // Auto-generate a preview once when the detail page opens, using the
  // default settings above.
  generatePdf();
}
