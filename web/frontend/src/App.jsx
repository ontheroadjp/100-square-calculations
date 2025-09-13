import { useState } from 'react'
import { useTranslation } from 'react-i18next';
import './App.css'; // Import App.css

function App() {
  const { t, i18n } = useTranslation();
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [paperSize, setPaperSize] = useState('A4');
  const [commandType, setCommandType] = useState('ope');
  const [aValue, setAValue] = useState('');
  const [bValue, setBValue] = useState('');
  const [aMin, setAMin] = useState(1);
  const [aMax, setAMax] = useState(9);
  const [bMin, setBMin] = useState(1);
  const [bMax, setBMax] = useState(9);
  const [operators, setOperators] = useState(['add']);
  const [descend, setDescend] = useState(false);
  const [reverse, setReverse] = useState(false);
  const [shuffle, setShuffle] = useState(false);
  const [intermediate, setIntermediate] = useState(false);
  const [rows, setRows] = useState(10);
  const [columns, setColumns] = useState(2);
  const [withBottomAnswer, setWithBottomAnswer] = useState(false);
  const [page, setPage] = useState(1);
  const [merge, setMerge] = useState(false);
  const [csv, setCsv] = useState(false);
  const [debug, setDebug] = useState(false);

  const [activeTab, setActiveTab] = useState('calculation'); // New state for active tab

  const handleOperatorChange = (op) => {
    setOperators([op]); // Set operators to an array with only the selected one
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setPdfUrl(null);

    const formData = {
      paper_size: paperSize,
      command_type: commandType,
      // Conditional a_value/b_value based on commandType
      ...(commandType === 'ope' && aValue && { a_value: parseInt(aValue) }),
      ...(commandType === 'ope' && bValue && { b_value: parseInt(bValue) }),
      ...(commandType === 'com' && aValue && { a_value: parseInt(aValue) }),
      ...(commandType === '99' && aValue && { a_value: parseInt(aValue) }),
      ...(commandType === 'squ' && aValue && { a_value: parseInt(aValue) }),
      ...(commandType === 'pi' && aValue && { a_value: parseInt(aValue) }),

      // Conditional a_min/max, b_min/max
      ...(commandType === 'ope' && { a_min: parseInt(aMin), a_max: parseInt(aMax), b_min: parseInt(bMin), b_max: parseInt(bMax) }),

      // Only include operator if commandType is 'ope' and an operator is selected
      ...(commandType === 'ope' && operators.length > 0 && { operator: operators }),

      // Conditional flags
      ...(commandType === 'ope' && intermediate && { intermediate: intermediate }),
      ...( (commandType === '99' || commandType === 'squ' || commandType === 'pi') && descend && { descend: descend }),
      ...( (commandType === '99' || commandType === 'squ' || commandType === 'pi') && reverse && { reverse: reverse }),
      ...( (commandType === '99' || commandType === 'squ' || commandType === 'pi') && shuffle && { shuffle: shuffle }),

      rows: parseInt(rows),
      columns: parseInt(columns),
      with_bottom_answer: withBottomAnswer,
      page: parseInt(page),
      merge: merge,
      csv: csv,
      debug: debug,
    };

    try {
      const response = await fetch('http://127.0.0.1:5000/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'PDF generation failed');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setActiveTab('pdf'); // Switch to PDF tab after successful generation

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isRequired = (field) => {
    if (field === 'a_value') {
      return ['com', '99', 'squ', 'pi'].includes(commandType);
    }
    // Add other required field logic here if needed
    return false;
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1>{t('app_title')}</h1>
        <div className="lang-switcher">
          <button
            onClick={() => changeLanguage('en')}
            className={i18n.language === 'en' ? 'active' : ''}
          >
            English
          </button>
          <button
            onClick={() => changeLanguage('ja')}
            className={i18n.language === 'ja' ? 'active' : ''}
          >
            日本語
          </button>
        </div>
      </header>

      {/* Main Content Area - Form */}
      <main className="main-content">
        <h2>{t('generate_worksheet')}</h2>
        <form onSubmit={handleSubmit} className="form-layout">
          {/* Command Type - Always at the top */}
          <div className="form-group">
            <label htmlFor="commandType">{t('command_type')}</label>
            <select
              id="commandType"
              value={commandType}
              onChange={(e) => {
                setCommandType(e.target.value);
                if (e.target.value !== 'ope') {
                  setOperators([]); // Clear operators if not 'ope'
                } else {
                  setOperators(['add']); // Default to 'add' if 'ope' is selected
                }

                // Set default aValue for 'com' and clear for 'ope'
                if (e.target.value === 'com') {
                  setAValue(100); // Default for complements
                } else if (e.target.value === 'ope') {
                  setAValue(''); // Clear aValue for 'ope'
                } else {
                  setAValue(''); // Clear for other types if not explicitly handled
                }
              }}
            >
              <option value="ope">{t('command_type_ope')}</option>
              <option value="com">{t('command_type_com')}</option>
              <option value="100">{t('command_type_100')}</option>
              <option value="99">{t('command_type_99')}</option>
              <option value="aBc">{t('command_type_aBc')}</option>
              <option value="squ">{t('command_type_squ')}</option>
              <option value="pi">{t('command_type_pi')}</option>
            </select>
          </div>

          {/* Tab Navigation */}
          <div className="tab-nav">
            <button type="button" className={activeTab === 'calculation' ? 'active' : ''} onClick={() => setActiveTab('calculation')}>{t('tab_calculation')}</button>
            <button type="button" className={activeTab === 'paper' ? 'active' : ''} onClick={() => setActiveTab('paper')}>{t('tab_paper')}</button>
            <button type="button" className={activeTab === 'options' ? 'active' : ''} onClick={() => setActiveTab('options')}>{t('tab_options')}</button>
            <button type="button" className={activeTab === 'pdf' ? 'active' : ''} onClick={() => setActiveTab('pdf')}>{t('tab_pdf')}</button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'calculation' && (
              <div className="tab-pane">
                {/* Number Ranges / Values */}
                {(commandType === 'ope' || commandType === 'com' || commandType === '100' || commandType === '99' || commandType === 'squ' || commandType === 'pi') && (
                  <div className="form-grid">
                    {(commandType === 'ope') && (
                      <>
                        <div className="form-group">
                          <label htmlFor="aMin">{t('a_min')}</label>
                          <input type="number" id="aMin" value={aMin} onChange={(e) => setAMin(e.target.value)} />
                        </div>
                        <div className="form-group">
                          <label htmlFor="aMax">{t('a_max')}</label>
                          <input type="number" id="aMax" value={aMax} onChange={(e) => setAMax(e.target.value)} />
                        </div>
                        <div className="form-group">
                          <label htmlFor="bMin">{t('b_min')}</label>
                          <input type="number" id="bMin" value={bMin} onChange={(e) => setBMin(e.target.value)} />
                        </div>
                        <div className="form-group">
                          <label htmlFor="bMax">{t('b_max')}</label>
                          <input type="number" id="bMax" value={bMax} onChange={(e) => setBMax(e.target.value)} />
                        </div>
                      </>
                    )}
                    {(commandType === 'ope' || commandType === '100') && (
                      <>
                        <div className="form-group">
                          <label htmlFor="aValue">{t('a_value')}{!isRequired('a_value') && <span className="optional-text"> ({t('optional')})</span>}</label>
                          <input type="number" id="aValue" value={aValue} onChange={(e) => setAValue(e.target.value)} />
                        </div>
                        <div className="form-group">
                          <label htmlFor="bValue">{t('b_value')}{!isRequired('b_value') && <span className="optional-text"> ({t('optional')})</span>}</label>
                          <input type="number" id="bValue" value={bValue} onChange={(e) => setBValue(e.target.value)} />
                        </div>
                      </>
                    )}
                    {(commandType === 'com' || commandType === '99' || commandType === 'squ' || commandType === 'pi') && (
                      <div className="form-group">
                        <label htmlFor="aValue">{t('a_value')}<span className="required-text"> ({t('required')})</span></label>
                        <input type="number" id="aValue" value={aValue} onChange={(e) => setAValue(e.target.value)} />
                      </div>
                    )}
                  </div>
                )}

                {/* Operators */}
                {commandType === 'ope' && (
                  <div className="form-group">
                    <label>{t('operators')}</label>
                    <div className="checkbox-grid">
                      {[ 'add', 'sub', 'mul', 'div', 'mix' ].map(op => (
                        <div key={op} className="checkbox-group">
                          <input
                            id={`op-${op}`}
                            type="radio"
                            name="operatorSelection"
                            checked={operators[0] === op}
                            onChange={() => setOperators([op])}
                            disabled={commandType !== 'ope'} // Disable if not 'ope'
                          />
                          <label htmlFor={`op-${op}`}>
                            {t(`operator_${op}`)}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Descend, Reverse, Shuffle for 99, squ, pi */}
                {(commandType === '99' || commandType === 'squ' || commandType === 'pi') && (
                  <div className="form-grid">
                    <div className="checkbox-group">
                      <input id="descend" type="checkbox" checked={descend} onChange={(e) => setDescend(e.target.checked)} />
                      <label htmlFor="descend">{t('descending_order')}</label>
                    </div>
                    <div className="checkbox-group">
                      <input id="reverse" type="checkbox" checked={reverse} onChange={(e) => setReverse(e.target.checked)} />
                      <label htmlFor="reverse">{t('reverse_order')}</label>
                    </div>
                    <div className="checkbox-group">
                      <input id="shuffle" type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} />
                      <label htmlFor="shuffle">{t('random_order')}</label>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'paper' && (
              <div className="tab-pane">
                {/* Paper Size (moved from top) */}
                <div className="form-group">
                  <label htmlFor="paperSize">{t('paper_size')}</label>
                  <select
                    id="paperSize"
                    value={paperSize}
                    onChange={(e) => setPaperSize(e.target.value)}
                  >
                    <option value="A4">{t('paper_size_a4')}</option>
                    <option value="A3">{t('paper_size_a3')}</option>
                    <option value="B5">{t('paper_size_b5')}</option>
                    <option value="a4l">{t('paper_size_a4l')}</option>
                  </select>
                </div>

                {/* Rows, Columns, Pages */}
                <div className="form-grid">
                  <div className="form-group">
                    <label htmlFor="rows">{t('rows_per_page')}</label>
                    <input type="number" id="rows" value={rows} onChange={(e) => setRows(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label htmlFor="columns">{t('columns_per_page')}</label>
                    <input type="number" id="columns" value={columns} onChange={(e) => setColumns(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label htmlFor="page">{t('number_of_pages')}</label>
                    <input type="number" id="page" value={page} onChange={(e) => setPage(e.target.value)} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'options' && (
              <div className="tab-pane">
                <div className="form-grid">
                  {/* Intermediate for ope */}
                  {commandType === 'ope' && (
                    <div className="checkbox-group">
                      <input id="intermediate" type="checkbox" checked={intermediate} onChange={(e) => setIntermediate(e.target.checked)} />
                      <label htmlFor="intermediate">{t('show_intermediate_formula')}</label>
                    </div>
                  )}
                  {/* Checkbox Options (moved from main form) */}
                  <div className="checkbox-group">
                    <input id="withBottomAnswer" type="checkbox" checked={withBottomAnswer} onChange={(e) => setWithBottomAnswer(e.target.checked)} />
                    <label htmlFor="withBottomAnswer">{t('include_bottom_answer')}</label>
                  </div>
                  <div className="checkbox-group">
                    <input id="merge" type="checkbox" checked={merge} onChange={(e) => setMerge(e.target.checked)} />
                    <label htmlFor="merge">{t('merge_answer_file')}</label>
                  </div>
                  <div className="checkbox-group">
                    <input id="csv" type="checkbox" checked={csv} onChange={(e) => setCsv(e.target.checked)} />
                    <label htmlFor="csv">{t('output_csv_raw_data')}</label>
                  </div>
                  <div className="checkbox-group">
                    <input id="debug" type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
                    <label htmlFor="debug">{t('debug_mode')}</label>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'pdf' && (
              <div className="tab-pane">
                {error && (
                  <div className="error-message">
                    {t('error_prefix')} {error}
                  </div>
                )}

                {pdfUrl && (
                  <div className="result-display">
                    <h3>{t('generated_pdf')}</h3>
                    <a
                      href={pdfUrl}
                      download="generated_worksheet.pdf"
                      className="download-button"
                    >
                      {t('download_pdf')}
                    </a>
                    <div className="pdf-iframe-container">
                      <iframe src={pdfUrl} className="pdf-iframe"></iframe>
                    </div>
                  </div>
                )}
                {!pdfUrl && !error && (
                  <p className="no-pdf-message">{t('no_pdf_generated')}</p>
                )}
              </div>
            )}
          </div>

          <div className="submit-button-container">
            <button
              type="submit"
              className="submit-button"
              disabled={loading}
            >
              {loading ? t('generating') : t('generate_pdf')}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

export default App;