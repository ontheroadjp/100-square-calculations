import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next';
import { GRADES, UNGRADED, CUSTOM_GRADE, presetsByGrade } from './drillPresets';
import CustomGenerator from './CustomGenerator';

// Maps the simplified "problem density" choice to nuts_calc.py's rows/columns.
// 'standard' matches the previous hardcoded default (10 rows x 2 columns).
const DENSITY_OPTIONS = [
  { value: 'few', labelKey: 'density_few', rows: 5, columns: 2 },
  { value: 'standard', labelKey: 'density_standard', rows: 10, columns: 2 },
  { value: 'many', labelKey: 'density_many', rows: 10, columns: 4 },
];
const DEFAULT_DENSITY = 'standard';

// Grade-like nav entries shown before the "Custom" button: numbered grades
// 1-6, then the ungraded bucket for drills with no specific course-of-study
// grade anchor (see drillPresets.js).
const NAV_GRADES = [...GRADES, UNGRADED];

const buildFileName = (grade, preset) => `drill_grade${grade}_${preset.id}.pdf`;

function PresetDetail({ grade, preset, onBack }) {
  const { t } = useTranslation();
  // The 100-square preset renders a fixed 10x10 grid; nuts_calc.py ignores
  // rows/columns for that command type, so the density choice has no effect.
  const supportsDensity = preset.params.command_type !== '100';

  const [numberValue, setNumberValue] = useState(preset.numberInput?.default ?? null);
  const [paperSize, setPaperSize] = useState('A4');
  const [pageCount, setPageCount] = useState(1);
  const [density, setDensity] = useState(DEFAULT_DENSITY);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error
  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);
  // Snapshot of the settings the current pdfUrl was generated with, so
  // "Regenerate PDF" can stay disabled until the user actually changes one.
  const [lastGenerated, setLastGenerated] = useState(null);

  const generatePdf = async () => {
    const densityOption = DENSITY_OPTIONS.find((option) => option.value === density) ?? DENSITY_OPTIONS[1];

    setStatus('loading');
    setError(null);

    const requestBody = {
      paper_size: paperSize,
      rows: densityOption.rows,
      columns: densityOption.columns,
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
      setLastGenerated({ paperSize, pageCount, density, numberValue });
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  useEffect(() => {
    // Auto-generate a preview once when the detail page opens, using the
    // default settings above.
    generatePdf();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isDirty = !lastGenerated
    || lastGenerated.paperSize !== paperSize
    || lastGenerated.pageCount !== pageCount
    || lastGenerated.density !== density
    || lastGenerated.numberValue !== numberValue;

  return (
    <div className="preset-detail">
      <button type="button" className="back-button" onClick={onBack}>
        {t('back')}
      </button>

      <h3 className="preset-detail-title">{t(preset.titleKey)}</h3>

      {status === 'loading' && <p className="preset-detail-status">{t('generating')}</p>}
      {status === 'error' && <p className="preset-card-error">{t('error_prefix')} {error}</p>}
      {pdfUrl && (
        <div className="pdf-iframe-container">
          <iframe src={pdfUrl} className="pdf-iframe" title="pdf-preview"></iframe>
        </div>
      )}

      <div className="preset-detail-settings">
        {preset.numberInput && (
          <div className="form-group">
            <label htmlFor="detailNumberInput">{t(preset.numberInput.labelKey)}</label>
            <input
              id="detailNumberInput"
              type="number"
              min={preset.numberInput.min}
              max={preset.numberInput.max}
              value={numberValue}
              onChange={(e) => setNumberValue(parseInt(e.target.value, 10))}
            />
          </div>
        )}
        <div className="form-group">
          <label htmlFor="detailPaperSize">{t('paper_size')}</label>
          <select id="detailPaperSize" value={paperSize} onChange={(e) => setPaperSize(e.target.value)}>
            <option value="A4">{t('paper_size_a4')}</option>
            <option value="A3">{t('paper_size_a3')}</option>
            <option value="B5">{t('paper_size_b5')}</option>
            <option value="a4l">{t('paper_size_a4l')}</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="detailPageCount">{t('number_of_pages')}</label>
          <input
            id="detailPageCount"
            type="number"
            min="1"
            max="10"
            value={pageCount}
            onChange={(e) => setPageCount(parseInt(e.target.value, 10))}
          />
        </div>
        {supportsDensity && (
          <div className="form-group">
            <label htmlFor="detailDensity">{t('problem_density')}</label>
            <select id="detailDensity" value={density} onChange={(e) => setDensity(e.target.value)}>
              {DENSITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="preset-detail-actions">
        <button
          type="button"
          className="regenerate-button"
          onClick={generatePdf}
          disabled={status === 'loading' || !isDirty}
        >
          {status === 'loading' ? t('generating') : t('regenerate_pdf')}
        </button>
        {status === 'ready' && pdfUrl ? (
          <a
            href={pdfUrl}
            download={buildFileName(grade, preset)}
            className="preset-download-button"
          >
            {t('download_pdf')}
          </a>
        ) : (
          <button type="button" className="preset-download-button" disabled>
            {t('download_pdf')}
          </button>
        )}
      </div>
    </div>
  );
}

function PresetCard({ preset, onOpen }) {
  const { t } = useTranslation();

  return (
    <div className="preset-card">
      <h3 className="preset-card-title">{t(preset.titleKey)}</h3>
      <p className="preset-card-desc">{t(preset.descKey)}</p>
      <button type="button" className="preset-download-button" onClick={() => onOpen(preset)}>
        {t('generate_pdf')}
      </button>
    </div>
  );
}

function GradeDrills() {
  const { t } = useTranslation();
  const [selectedGrade, setSelectedGrade] = useState(1);
  const [openPreset, setOpenPreset] = useState(null);

  const isCustom = selectedGrade === CUSTOM_GRADE;

  const handleSelectGrade = (grade) => {
    setSelectedGrade(grade);
    setOpenPreset(null);
  };

  if (openPreset) {
    return (
      <div className="grade-drills">
        <PresetDetail grade={selectedGrade} preset={openPreset} onBack={() => setOpenPreset(null)} />
      </div>
    );
  }

  const writtenPresets = !isCustom ? presetsByGrade[selectedGrade].written : [];

  return (
    <div className="grade-drills">
      <p className="grade-drills-intro">{t('grade_drills_intro')}</p>
      <p className="grade-drills-disclaimer">{t('grade_drills_disclaimer')}</p>

      <nav className="grade-nav" aria-label={t('grade_select_label')}>
        {NAV_GRADES.map((grade) => (
          <button
            key={grade}
            type="button"
            className={`grade-link ${selectedGrade === grade ? 'active' : ''}`}
            onClick={() => handleSelectGrade(grade)}
          >
            {t(`grade_${grade}`)}
          </button>
        ))}
        <button
          type="button"
          className={`grade-link ${isCustom ? 'active' : ''}`}
          onClick={() => handleSelectGrade(CUSTOM_GRADE)}
        >
          {t('nav_custom')}
        </button>
      </nav>

      {isCustom ? (
        <CustomGenerator />
      ) : (
        <>
          <div className="preset-card-grid">
            {presetsByGrade[selectedGrade].normal.map((preset) => (
              <PresetCard key={preset.id} preset={preset} onOpen={setOpenPreset} />
            ))}
          </div>

          {writtenPresets.length > 0 && (
            <section className="written-section">
              <h3 className="written-section-title">{t('written_section_title')}</h3>
              <div className="preset-card-grid">
                {writtenPresets.map((preset) => (
                  <PresetCard key={preset.id} preset={preset} onOpen={setOpenPreset} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default GradeDrills;
