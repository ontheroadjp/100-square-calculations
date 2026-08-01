import { useState } from 'react'
import { useTranslation } from 'react-i18next';
import { GRADES, CUSTOM_GRADE, presetsByGrade } from './drillPresets';
import CustomGenerator from './CustomGenerator';

const DEFAULT_ROWS = 10;
const DEFAULT_COLUMNS = 2;

const buildFileName = (grade, preset) => `drill_grade${grade}_${preset.id}.pdf`;

function PresetCard({ grade, preset, paperSize, pageCount }) {
  const { t } = useTranslation();
  const [numberValue, setNumberValue] = useState(preset.numberInput?.default ?? null);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error
  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);

  // A synthetic anchor.click() fired after an `await` is not always treated
  // as a direct user gesture, and Chrome silently drops later automatic
  // downloads triggered that way. Generating first and letting the user
  // click a real <a download> link (same pattern as CustomGenerator) avoids
  // that failure mode.
  const handleGenerate = async () => {
    setStatus('loading');
    setError(null);
    setPdfUrl(null);

    const requestBody = {
      paper_size: paperSize,
      rows: DEFAULT_ROWS,
      columns: DEFAULT_COLUMNS,
      page: pageCount,
      ...preset.params,
      ...(preset.numberInput && { [preset.numberInput.param]: numberValue }),
    };

    try {
      const response = await fetch('http://127.0.0.1:5000/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error ?? 'PDF generation failed');
      }

      const blob = await response.blob();
      setPdfUrl(URL.createObjectURL(blob));
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  return (
    <div className="preset-card">
      <h3 className="preset-card-title">{t(preset.titleKey)}</h3>
      <p className="preset-card-desc">{t(preset.descKey)}</p>

      {preset.numberInput && (
        <div className="preset-card-number-input">
          <label htmlFor={`${preset.id}-number`}>{t(preset.numberInput.labelKey)}</label>
          <input
            id={`${preset.id}-number`}
            type="number"
            min={preset.numberInput.min}
            max={preset.numberInput.max}
            value={numberValue}
            onChange={(e) => setNumberValue(parseInt(e.target.value, 10))}
          />
        </div>
      )}

      {status === 'ready' && pdfUrl ? (
        <a
          href={pdfUrl}
          download={buildFileName(grade, preset)}
          className="preset-download-button"
          onClick={() => setStatus('idle')}
        >
          {t('download_pdf')}
        </a>
      ) : (
        <button
          type="button"
          className="preset-download-button"
          onClick={handleGenerate}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? t('generating') : t('generate_pdf')}
        </button>
      )}

      {status === 'error' && (
        <p className="preset-card-error">{t('error_prefix')} {error}</p>
      )}
    </div>
  );
}

function GradeDrills() {
  const { t } = useTranslation();
  const [selectedGrade, setSelectedGrade] = useState(1);
  const [paperSize, setPaperSize] = useState('A4');
  const [pageCount, setPageCount] = useState(1);

  const isCustom = selectedGrade === CUSTOM_GRADE;

  return (
    <div className="grade-drills">
      <p className="grade-drills-intro">{t('grade_drills_intro')}</p>
      <p className="grade-drills-disclaimer">{t('grade_drills_disclaimer')}</p>

      <nav className="grade-nav" aria-label={t('grade_select_label')}>
        {GRADES.map((grade) => (
          <button
            key={grade}
            type="button"
            className={`grade-link ${selectedGrade === grade ? 'active' : ''}`}
            onClick={() => setSelectedGrade(grade)}
          >
            {t(`grade_${grade}`)}
          </button>
        ))}
        <button
          type="button"
          className={`grade-link ${isCustom ? 'active' : ''}`}
          onClick={() => setSelectedGrade(CUSTOM_GRADE)}
        >
          {t('nav_custom')}
        </button>
      </nav>

      {isCustom ? (
        <CustomGenerator />
      ) : (
        <>
          <div className="grade-shared-settings">
            <div className="form-group">
              <label htmlFor="sharedPaperSize">{t('paper_size')}</label>
              <select id="sharedPaperSize" value={paperSize} onChange={(e) => setPaperSize(e.target.value)}>
                <option value="A4">{t('paper_size_a4')}</option>
                <option value="A3">{t('paper_size_a3')}</option>
                <option value="B5">{t('paper_size_b5')}</option>
                <option value="a4l">{t('paper_size_a4l')}</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="sharedPageCount">{t('number_of_pages')}</label>
              <input
                id="sharedPageCount"
                type="number"
                min="1"
                max="10"
                value={pageCount}
                onChange={(e) => setPageCount(parseInt(e.target.value, 10))}
              />
            </div>
          </div>

          <div className="preset-card-grid">
            {presetsByGrade[selectedGrade].map((preset) => (
              <PresetCard
                key={preset.id}
                grade={selectedGrade}
                preset={preset}
                paperSize={paperSize}
                pageCount={pageCount}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default GradeDrills;
