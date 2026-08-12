import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next';
import { GRADES, UNGRADED, CUSTOM_GRADE } from './drillPresets';
import CustomGenerator from './CustomGenerator';
import {
  addSearchText,
  buildDrillCatalog,
  DRILL_FORMS,
  filterDrillCatalog,
  NUMBER_TYPES,
} from './drillCatalog';
import {
  getVerticalRows,
  isVerticalOperation,
  VERTICAL_COLUMNS,
} from './verticalLayout';

// Maps the simplified "problem density" choice to nuts_calc.py's rows/columns.
// 'standard' matches the previous hardcoded default (10 rows x 2 columns).
const DENSITY_OPTIONS = [
  { value: 'few', labelKey: 'density_few', rows: 5, columns: 2 },
  { value: 'standard', labelKey: 'density_standard', rows: 10, columns: 2 },
  { value: 'many', labelKey: 'density_many', rows: 10, columns: 4 },
];
const DEFAULT_DENSITY = 'standard';
const NUMBER_TYPE_GROUPS = {
  integers: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  decimals: ['addition-subtraction', 'multiplication-division', 'four-operations'],
  fractions: ['addition-subtraction', 'multiplication-division', 'comparison'],
};
const INTEGER_FORMAT_FILTERS = ['parentheses', 'missing-value'];

const buildFileName = (grade, preset) => `drill_grade${grade}_${preset.id}.pdf`;

function PresetDetail({ grade, preset, onBack }) {
  const { t } = useTranslation();
  // The 100-square preset renders a fixed 10x10 grid; nuts_calc.py ignores
  // rows/columns for that command type, so the density choice has no effect.
  const isVerticalPreset = isVerticalOperation(preset.params);
  const supportsDensity = preset.params.command_type !== '100' && !isVerticalPreset;

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
    const layout = isVerticalPreset
      ? { rows: getVerticalRows(paperSize), columns: VERTICAL_COLUMNS }
      : densityOption;

    setStatus('loading');
    setError(null);

    const requestBody = {
      paper_size: paperSize,
      rows: layout.rows,
      columns: layout.columns,
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

function DrillCard({ drill, onOpen, onSelectGrade, onSelectLevel }) {
  const { t } = useTranslation();
  const formats = Object.entries(drill.presets);

  return (
    <article className="preset-card">
      <div className="drill-badges">
        <button type="button" className="drill-badge grade-badge" onClick={() => onSelectGrade(drill.grade)}>
          {t(`grade_${drill.grade}`)}
        </button>
        <button type="button" className="drill-badge level-badge" onClick={() => onSelectLevel(drill.level)}>
          {t(`level_${drill.level}`)}
        </button>
      </div>
      <h3 className="preset-card-title">{t(drill.titleKey)}</h3>
      <p className="preset-card-desc">{t(drill.descKey)}</p>
      <div className="drill-card-actions">
        {formats.map(([format, preset]) => (
          <button key={format} type="button" className="preset-download-button" onClick={() => onOpen(drill.grade, preset)}>
            {formats.length > 1 ? t(`format_${format}`) : t('generate_pdf')}
          </button>
        ))}
      </div>
    </article>
  );
}

function DrillGrid({ drills, onOpen, onSelectGrade, onSelectLevel }) {
  const { t } = useTranslation();
  if (drills.length === 0) return <p className="drill-empty-state">{t('no_drills_found')}</p>;

  return (
    <div className="preset-card-grid">
      {drills.map((drill) => <DrillCard key={drill.id} drill={drill} onOpen={onOpen} onSelectGrade={onSelectGrade} onSelectLevel={onSelectLevel} />)}
    </div>
  );
}

function NumberTypeCatalog({ catalog, availableCatalog, numberType, forms, onToggleForm, onOpen, onSelectGrade, onSelectLevel }) {
  const { t } = useTranslation();
  const groups = NUMBER_TYPE_GROUPS[numberType];
  const availableForms = numberType === 'integers'
    ? INTEGER_FORMAT_FILTERS.filter((form) => availableCatalog.some((drill) => drill.forms.includes(form)))
    : [];

  return (
    <>
      <header className="number-type-header">
        <h1>{t(`number_type_${numberType}`)}</h1>
        <p>{t(`number_type_${numberType}_intro`)}</p>
      </header>
      {availableForms.length > 0 && (
        <fieldset className="format-filter" aria-label={t('format_filter_label')}>
          <legend>{t('format_filter_label')}</legend>
          {availableForms.map((form) => (
            <label key={form}>
              <input type="checkbox" checked={forms.includes(form)} onChange={() => onToggleForm(form)} />
              {t(`form_${form}`)}
            </label>
          ))}
        </fieldset>
      )}
      {groups ? groups.map((group) => {
        const drills = catalog.filter((drill) => drill.operationGroup === group);
        if (drills.length === 0) return null;
        return (
          <section key={group} className="number-type-section">
            <h2>{t(`operation_group_${group}`)}</h2>
            <p>{t(`operation_group_${group}_desc`)}</p>
            <DrillGrid drills={drills} onOpen={onOpen} onSelectGrade={onSelectGrade} onSelectLevel={onSelectLevel} />
          </section>
        );
      }) : <DrillGrid drills={catalog} onOpen={onOpen} onSelectGrade={onSelectGrade} onSelectLevel={onSelectLevel} />}
    </>
  );
}

function GradeDrills() {
  const { t } = useTranslation();
  const [route, setRoute] = useState('home');
  const [selectedNumberType, setSelectedNumberType] = useState(null);
  const [selectedForms, setSelectedForms] = useState([]);
  const [selectedGrade, setSelectedGrade] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [query, setQuery] = useState('');
  const [openPreset, setOpenPreset] = useState(null);
  const [activeRenderer, setActiveRenderer] = useState('reportlab');
  const supportsWritten = activeRenderer === 'latex';

  useEffect(() => {
    fetch('http://127.0.0.1:5000/renderer-info')
      .then((response) => response.json())
      .then((data) => setActiveRenderer(data.renderer))
      .catch(() => setActiveRenderer('reportlab'));
  }, []);

  const openCatalog = ({ numberType = null, forms = [], grade = null, level = null } = {}) => {
    setRoute('catalog');
    setSelectedNumberType(numberType);
    setSelectedForms(forms);
    setSelectedGrade(grade);
    setSelectedLevel(level);
  };

  const toggleForm = (form) => {
    setSelectedForms((forms) => (forms.includes(form)
      ? forms.filter((candidate) => candidate !== form)
      : [...forms, form]));
  };

  if (openPreset) {
    return <div className="grade-drills"><PresetDetail grade={openPreset.grade} preset={openPreset.preset} onBack={() => setOpenPreset(null)} /></div>;
  }

  if (route === CUSTOM_GRADE) return <CustomGenerator supportsVertical={supportsWritten} />;

  const catalog = addSearchText(buildDrillCatalog(activeRenderer), t);
  const filteredDrills = filterDrillCatalog(catalog, {
    numberType: selectedNumberType,
    forms: selectedForms,
    grade: selectedGrade,
    level: selectedLevel,
    query,
  });
  const availableNumberTypeDrills = filterDrillCatalog(catalog, {
    numberType: selectedNumberType,
    grade: selectedGrade,
    level: selectedLevel,
    query,
  });
  const availableHomeForms = DRILL_FORMS.filter((form) => catalog.some((drill) => drill.forms.includes(form)));
  const showCatalog = route === 'catalog' || query.trim() !== '';

  return (
    <div className="grade-drills">
      <div className="drill-search">
        <label htmlFor="drillSearch">{t('drill_search_label')}</label>
        <input id="drillSearch" type="search" value={query} onChange={(event) => { setQuery(event.target.value); openCatalog({}); }} placeholder={t('drill_search_placeholder')} />
      </div>
      <nav className="grade-nav" aria-label={t('drill_navigation_label')}>
        <button type="button" className={`grade-link ${route === 'home' ? 'active' : ''}`} onClick={() => { setRoute('home'); setQuery(''); }}>{t('nav_home')}</button>
        <button type="button" className={`grade-link ${route === CUSTOM_GRADE ? 'active' : ''}`} onClick={() => setRoute(CUSTOM_GRADE)}>{t('nav_custom')}</button>
      </nav>

      {showCatalog ? (
        <>
          <div className="drill-filter-bar" aria-label={t('drill_filter_label')}>
            <select aria-label={t('number_type_filter_label')} value={selectedNumberType ?? ''} onChange={(event) => setSelectedNumberType(event.target.value || null)}>
              <option value="">{t('all_number_types')}</option>
              {NUMBER_TYPES.map((numberType) => <option key={numberType} value={numberType}>{t(`number_type_${numberType}`)}</option>)}
            </select>
            <select aria-label={t('grade_select_label')} value={selectedGrade ?? ''} onChange={(event) => setSelectedGrade(event.target.value === '' ? null : (event.target.value === UNGRADED ? UNGRADED : Number(event.target.value)))}>
              <option value="">{t('all_grades')}</option>
              {GRADES.map((grade) => <option key={grade} value={grade}>{t(`grade_${grade}`)}</option>)}
              <option value={UNGRADED}>{t(`grade_${UNGRADED}`)}</option>
            </select>
            <select aria-label={t('level_filter_label')} value={selectedLevel ?? ''} onChange={(event) => setSelectedLevel(event.target.value || null)}>
              <option value="">{t('all_levels')}</option>
              {['basic', 'standard', 'advanced', 'exam-prep'].map((level) => <option key={level} value={level}>{t(`level_${level}`)}</option>)}
            </select>
            <button type="button" className="filter-reset" onClick={() => openCatalog()}>{t('clear_filters')}</button>
          </div>
          {selectedNumberType && !query.trim() ? (
            <NumberTypeCatalog
              catalog={filteredDrills}
              availableCatalog={availableNumberTypeDrills}
              numberType={selectedNumberType}
              forms={selectedForms}
              onToggleForm={toggleForm}
              onOpen={(grade, preset) => setOpenPreset({ grade, preset })}
              onSelectGrade={(grade) => openCatalog({ numberType: selectedNumberType, forms: selectedForms, grade, level: selectedLevel })}
              onSelectLevel={(level) => openCatalog({ numberType: selectedNumberType, forms: selectedForms, grade: selectedGrade, level })}
            />
          ) : <DrillGrid drills={filteredDrills} onOpen={(grade, preset) => setOpenPreset({ grade, preset })} onSelectGrade={(grade) => openCatalog({ grade, level: selectedLevel })} onSelectLevel={(level) => openCatalog({ grade: selectedGrade, level })} />}
        </>
      ) : (
        <>
          <p className="grade-drills-intro">{t('drill_home_intro')}</p>
          <section className="drill-home-section">
            <h2>{t('number_type_start_title')}</h2>
            <div className="drill-start-grid">
              {NUMBER_TYPES.map((numberType) => <button key={numberType} type="button" className="drill-start-card" onClick={() => openCatalog({ numberType })}>{t(`number_type_${numberType}`)}</button>)}
            </div>
          </section>
          <section className="drill-home-section">
            <h2>{t('form_start_title')}</h2>
            <div className="drill-start-grid">
              {availableHomeForms.map((form) => <button key={form} type="button" className="drill-start-card" onClick={() => openCatalog({ forms: [form] })}>{t(`form_${form}`)}</button>)}
            </div>
          </section>
          <section className="drill-home-section">
            <h2>{t('grade_start_title')}</h2>
            <div className="drill-start-grid grade-start-grid">
              {[...GRADES, UNGRADED].map((grade) => <button key={grade} type="button" className="drill-start-card" onClick={() => openCatalog({ grade })}>{t(`grade_${grade}`)}</button>)}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default GradeDrills;
