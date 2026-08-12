import { t } from './strings.js';
import { getVerticalRows, VERTICAL_COLUMNS } from './verticalLayout.js';

const API_BASE = 'http://127.0.0.1:5000';

export function mountCustomGenerator(container, { supportsVertical = false } = {}) {
  const state = {
    pdfUrl: null,
    loading: false,
    error: null,
    paperSize: 'A4',
    commandType: 'ope',
    aValue: '',
    bValue: '',
    aMin: 1,
    aMax: 9,
    bMin: 1,
    bMax: 9,
    operators: ['add'],
    descend: false,
    reverse: false,
    shuffle: false,
    intermediate: false,
    vertical: false,
    rows: 10,
    columns: 2,
    withBottomAnswer: false,
    page: 1,
    merge: false,
    csv: false,
    debug: false,
    activeTab: 'calculation',
  };

  const isRequired = (field) => {
    if (field === 'a_value') {
      return ['com', '99', 'squ', 'pi'].includes(state.commandType);
    }
    return false;
  };

  const enableVerticalLayout = (nextPaperSize) => {
    state.rows = getVerticalRows(nextPaperSize);
    state.columns = VERTICAL_COLUMNS;
  };

  async function handleSubmit(event) {
    event.preventDefault();
    state.loading = true;
    state.error = null;
    state.pdfUrl = null;
    render();

    const { commandType } = state;
    const formData = {
      paper_size: state.paperSize,
      command_type: commandType,
      ...(commandType === 'ope' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),
      ...(commandType === 'ope' && state.bValue !== '' && { b_value: parseInt(state.bValue, 10) }),
      ...(commandType === '100' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),
      ...(commandType === '100' && state.bValue !== '' && { b_value: parseInt(state.bValue, 10) }),
      ...(commandType === 'com' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),
      ...(commandType === '99' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),
      ...(commandType === 'squ' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),
      ...(commandType === 'pi' && state.aValue !== '' && { a_value: parseInt(state.aValue, 10) }),

      ...(commandType === 'ope' && {
        a_min: parseInt(state.aMin, 10),
        a_max: parseInt(state.aMax, 10),
        b_min: parseInt(state.bMin, 10),
        b_max: parseInt(state.bMax, 10),
      }),

      ...(commandType === 'ope' && state.operators.length > 0 && { operator: state.operators }),

      ...(commandType === 'ope' && state.intermediate && { intermediate: state.intermediate }),
      ...(commandType === 'ope' && state.vertical && { vertical: state.vertical }),
      ...(['99', 'squ', 'pi'].includes(commandType) && state.descend && { descend: state.descend }),
      ...(['99', 'squ', 'pi'].includes(commandType) && state.reverse && { reverse: state.reverse }),
      ...(['99', 'squ', 'pi'].includes(commandType) && state.shuffle && { shuffle: state.shuffle }),

      rows: parseInt(state.rows, 10),
      columns: parseInt(state.columns, 10),
      with_bottom_answer: state.withBottomAnswer,
      page: parseInt(state.page, 10),
      merge: state.merge,
      csv: state.csv,
      debug: state.debug,
    };

    try {
      const response = await fetch(`${API_BASE}/generate-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'PDF generation failed');
      }

      const blob = await response.blob();
      state.pdfUrl = URL.createObjectURL(blob);
      state.activeTab = 'pdf';
    } catch (err) {
      state.error = err.message;
    } finally {
      state.loading = false;
    }
    render();
  }

  function render() {
    const { commandType } = state;
    const showRanges = ['ope', 'com', '100', '99', 'squ', 'pi'].includes(commandType);
    const showAValueRequired = ['com', '99', 'squ', 'pi'].includes(commandType);

    container.innerHTML = `
      <div class="custom-generator">
        <h2>${t('generate_worksheet')}</h2>
        <form class="form-layout" data-role="generator-form">
          <div class="form-group">
            <label for="commandType">${t('command_type')}</label>
            <select id="commandType" data-role="command-type">
              <option value="ope" ${commandType === 'ope' ? 'selected' : ''}>${t('command_type_ope')}</option>
              <option value="com" ${commandType === 'com' ? 'selected' : ''}>${t('command_type_com')}</option>
              <option value="100" ${commandType === '100' ? 'selected' : ''}>${t('command_type_100')}</option>
              <option value="99" ${commandType === '99' ? 'selected' : ''}>${t('command_type_99')}</option>
              <option value="aBc" ${commandType === 'aBc' ? 'selected' : ''}>${t('command_type_aBc')}</option>
              <option value="squ" ${commandType === 'squ' ? 'selected' : ''}>${t('command_type_squ')}</option>
              <option value="pi" ${commandType === 'pi' ? 'selected' : ''}>${t('command_type_pi')}</option>
            </select>
          </div>

          <div class="tab-nav">
            <button type="button" data-action="tab" data-tab="calculation" class="${state.activeTab === 'calculation' ? 'active' : ''}">${t('tab_calculation')}</button>
            <button type="button" data-action="tab" data-tab="paper" class="${state.activeTab === 'paper' ? 'active' : ''}">${t('tab_paper')}</button>
            <button type="button" data-action="tab" data-tab="options" class="${state.activeTab === 'options' ? 'active' : ''}">${t('tab_options')}</button>
            <button type="button" data-action="tab" data-tab="pdf" class="${state.activeTab === 'pdf' ? 'active' : ''}">${t('tab_pdf')}</button>
          </div>

          <div class="tab-content">
            ${state.activeTab === 'calculation' ? `
              <div class="tab-pane">
                ${showRanges ? `
                  <div class="form-grid">
                    ${commandType === 'ope' ? `
                      <div class="form-group">
                        <label for="aMin">${t('a_min')}</label>
                        <input type="number" id="aMin" data-role="a-min" value="${state.aMin}">
                      </div>
                      <div class="form-group">
                        <label for="aMax">${t('a_max')}</label>
                        <input type="number" id="aMax" data-role="a-max" value="${state.aMax}">
                      </div>
                      <div class="form-group">
                        <label for="bMin">${t('b_min')}</label>
                        <input type="number" id="bMin" data-role="b-min" value="${state.bMin}">
                      </div>
                      <div class="form-group">
                        <label for="bMax">${t('b_max')}</label>
                        <input type="number" id="bMax" data-role="b-max" value="${state.bMax}">
                      </div>
                    ` : ''}
                    ${(commandType === 'ope' || commandType === '100') ? `
                      <div class="form-group">
                        <label for="aValue">${t('a_value')}<span class="optional-text"> (${t('optional')})</span></label>
                        <input type="number" id="aValue" data-role="a-value" value="${state.aValue}">
                      </div>
                      <div class="form-group">
                        <label for="bValue">${t('b_value')}<span class="optional-text"> (${t('optional')})</span></label>
                        <input type="number" id="bValue" data-role="b-value" value="${state.bValue}">
                      </div>
                    ` : ''}
                    ${showAValueRequired ? `
                      <div class="form-group">
                        <label for="aValue">${t('a_value')}<span class="required-text"> (${t('required')})</span></label>
                        <input type="number" id="aValue" data-role="a-value" value="${state.aValue}">
                      </div>
                    ` : ''}
                  </div>
                ` : ''}

                ${commandType === 'ope' ? `
                  <div class="form-group">
                    <label>${t('operators')}</label>
                    <div class="checkbox-grid">
                      ${['add', 'sub', 'mul', 'div', 'mix'].map((op) => `
                        <div class="checkbox-group">
                          <input id="op-${op}" type="radio" name="operatorSelection" data-role="operator" value="${op}" ${state.operators[0] === op ? 'checked' : ''}>
                          <label for="op-${op}">${t(`operator_${op}`)}</label>
                        </div>
                      `).join('')}
                    </div>
                  </div>
                ` : ''}

                ${['99', 'squ', 'pi'].includes(commandType) ? `
                  <div class="form-grid">
                    <div class="checkbox-group">
                      <input id="descend" type="checkbox" data-role="descend" ${state.descend ? 'checked' : ''}>
                      <label for="descend">${t('descending_order')}</label>
                    </div>
                    <div class="checkbox-group">
                      <input id="reverse" type="checkbox" data-role="reverse" ${state.reverse ? 'checked' : ''}>
                      <label for="reverse">${t('reverse_order')}</label>
                    </div>
                    <div class="checkbox-group">
                      <input id="shuffle" type="checkbox" data-role="shuffle" ${state.shuffle ? 'checked' : ''}>
                      <label for="shuffle">${t('random_order')}</label>
                    </div>
                  </div>
                ` : ''}
              </div>
            ` : ''}

            ${state.activeTab === 'paper' ? `
              <div class="tab-pane">
                <div class="form-group">
                  <label for="paperSize">${t('paper_size')}</label>
                  <select id="paperSize" data-role="paper-size">
                    <option value="A4" ${state.paperSize === 'A4' ? 'selected' : ''}>${t('paper_size_a4')}</option>
                    <option value="A3" ${state.paperSize === 'A3' ? 'selected' : ''}>${t('paper_size_a3')}</option>
                    <option value="B5" ${state.paperSize === 'B5' ? 'selected' : ''}>${t('paper_size_b5')}</option>
                    <option value="a4l" ${state.paperSize === 'a4l' ? 'selected' : ''}>${t('paper_size_a4l')}</option>
                  </select>
                </div>
                <div class="form-grid">
                  <div class="form-group">
                    <label for="rows">${t('rows_per_page')}</label>
                    <input type="number" id="rows" data-role="rows" value="${state.rows}">
                  </div>
                  <div class="form-group">
                    <label for="columns">${t('columns_per_page')}</label>
                    <input type="number" id="columns" data-role="columns" value="${state.columns}">
                  </div>
                  <div class="form-group">
                    <label for="page">${t('number_of_pages')}</label>
                    <input type="number" id="page" data-role="page" value="${state.page}">
                  </div>
                </div>
              </div>
            ` : ''}

            ${state.activeTab === 'options' ? `
              <div class="tab-pane">
                <div class="form-grid">
                  ${commandType === 'ope' ? `
                    <div class="checkbox-group">
                      <input id="intermediate" type="checkbox" data-role="intermediate" ${state.intermediate ? 'checked' : ''}>
                      <label for="intermediate">${t('show_intermediate_formula')}</label>
                    </div>
                  ` : ''}
                  ${commandType === 'ope' && supportsVertical ? `
                    <div class="checkbox-group">
                      <input id="vertical" type="checkbox" data-role="vertical" ${state.vertical ? 'checked' : ''}>
                      <label for="vertical">${t('vertical_format')}</label>
                    </div>
                  ` : ''}
                  <div class="checkbox-group">
                    <input id="withBottomAnswer" type="checkbox" data-role="with-bottom-answer" ${state.withBottomAnswer ? 'checked' : ''}>
                    <label for="withBottomAnswer">${t('include_bottom_answer')}</label>
                  </div>
                  <div class="checkbox-group">
                    <input id="merge" type="checkbox" data-role="merge" ${state.merge ? 'checked' : ''}>
                    <label for="merge">${t('merge_answer_file')}</label>
                  </div>
                  <div class="checkbox-group">
                    <input id="csv" type="checkbox" data-role="csv" ${state.csv ? 'checked' : ''}>
                    <label for="csv">${t('output_csv_raw_data')}</label>
                  </div>
                  <div class="checkbox-group">
                    <input id="debug" type="checkbox" data-role="debug" ${state.debug ? 'checked' : ''}>
                    <label for="debug">${t('debug_mode')}</label>
                  </div>
                </div>
              </div>
            ` : ''}

            ${state.activeTab === 'pdf' ? `
              <div class="tab-pane">
                ${state.error ? `<div class="error-message">${t('error_prefix')} ${state.error}</div>` : ''}
                ${state.pdfUrl ? `
                  <div class="result-display">
                    <h3>${t('generated_pdf')}</h3>
                    <a href="${state.pdfUrl}" download="generated_worksheet.pdf" class="download-button">${t('download_pdf')}</a>
                    <div class="pdf-iframe-container">
                      <iframe src="${state.pdfUrl}" class="pdf-iframe" title="generated-pdf-preview"></iframe>
                    </div>
                  </div>
                ` : ''}
                ${!state.pdfUrl && !state.error ? `<p class="no-pdf-message">${t('no_pdf_generated')}</p>` : ''}
              </div>
            ` : ''}
          </div>

          <div class="submit-button-container">
            <button type="submit" class="submit-button" ${state.loading ? 'disabled' : ''}>
              ${state.loading ? t('generating') : t('generate_pdf')}
            </button>
          </div>
        </form>
      </div>
    `;
  }

  container.addEventListener('submit', (event) => {
    if (event.target.dataset.role === 'generator-form') handleSubmit(event);
  });

  container.addEventListener('click', (event) => {
    const actionEl = event.target.closest('[data-action="tab"]');
    if (actionEl) {
      state.activeTab = actionEl.dataset.tab;
      render();
    }
  });

  container.addEventListener('input', (event) => {
    const role = event.target.dataset.role;
    const numericRoles = ['a-min', 'a-max', 'b-min', 'b-max', 'rows', 'columns', 'page'];
    const stringRoles = { 'a-value': 'aValue', 'b-value': 'bValue' };
    const camelCase = {
      'a-min': 'aMin', 'a-max': 'aMax', 'b-min': 'bMin', 'b-max': 'bMax',
      rows: 'rows', columns: 'columns', page: 'page',
    };
    if (numericRoles.includes(role)) {
      state[camelCase[role]] = event.target.value;
    } else if (role in stringRoles) {
      state[stringRoles[role]] = event.target.value;
    }
  });

  container.addEventListener('change', (event) => {
    const role = event.target.dataset.role;
    if (role === 'command-type') {
      const value = event.target.value;
      state.commandType = value;
      state.operators = value === 'ope' ? ['add'] : [];
      state.aValue = value === 'com' ? 100 : '';
      render();
    } else if (role === 'operator') {
      state.operators = [event.target.value];
    } else if (role === 'descend') {
      state.descend = event.target.checked;
    } else if (role === 'reverse') {
      state.reverse = event.target.checked;
    } else if (role === 'shuffle') {
      state.shuffle = event.target.checked;
    } else if (role === 'paper-size') {
      state.paperSize = event.target.value;
      if (state.vertical) enableVerticalLayout(state.paperSize);
      render();
    } else if (role === 'intermediate') {
      state.intermediate = event.target.checked;
    } else if (role === 'vertical') {
      state.vertical = event.target.checked;
      if (state.vertical) enableVerticalLayout(state.paperSize);
    } else if (role === 'with-bottom-answer') {
      state.withBottomAnswer = event.target.checked;
    } else if (role === 'merge') {
      state.merge = event.target.checked;
    } else if (role === 'csv') {
      state.csv = event.target.checked;
    } else if (role === 'debug') {
      state.debug = event.target.checked;
    }
  });

  render();
}
