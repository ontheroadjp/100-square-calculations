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

  const handleOperatorChange = (op) => {
    setOperators(prev =>
      prev.includes(op) ? prev.filter(item => item !== op) : [...prev, op]
    );
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
      ...(aValue && { a_value: parseInt(aValue) }),
      ...(bValue && { b_value: parseInt(bValue) }),
      a_min: parseInt(aMin),
      a_max: parseInt(aMax),
      b_min: parseInt(bMin),
      b_max: parseInt(bMax),
      operator: operators,
      descend: descend,
      reverse: reverse,
      shuffle: shuffle,
      intermediate: intermediate,
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

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
          {/* Paper Size */}
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

          {/* Command Type */}
          <div className="form-group">
            <label htmlFor="commandType">{t('command_type')}</label>
            <select
              id="commandType"
              value={commandType}
              onChange={(e) => setCommandType(e.target.value)}
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

          {/* Number Ranges / Values */}
          <div className="form-grid">
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
            <div className="form-group">
              <label htmlFor="aValue">{t('a_value')}</label>
              <input type="number" id="aValue" value={aValue} onChange={(e) => setAValue(e.target.value)} placeholder={t('optional')} />
            </div>
            <div className="form-group">
              <label htmlFor="bValue">{t('b_value')}</label>
              <input type="number" id="bValue" value={bValue} onChange={(e) => setBValue(e.target.value)} placeholder={t('optional')} />
            </div>
          </div>

          {/* Operators */}
          <div className="form-group">
            <label>{t('operators')}</label>
            <div className="checkbox-grid">
              {[ 'add', 'sub', 'mul', 'div', 'mix' ].map(op => (
                <div key={op} className="checkbox-group">
                  <input
                    id={`op-${op}`}
                    type="checkbox"
                    checked={operators.includes(op)}
                    onChange={() => handleOperatorChange(op)}
                  />
                  <label htmlFor={`op-${op}`}>
                    {t(`operator_${op}`)}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Other Options */}
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

          {/* Checkbox Options */}
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
            <div className="checkbox-group">
              <input id="intermediate" type="checkbox" checked={intermediate} onChange={(e) => setIntermediate(e.target.checked)} />
              <label htmlFor="intermediate">{t('show_intermediate_formula')}</label>
            </div>
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

        {/* Result Display */}
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
      </main>
    </div>
  );
}

export default App;