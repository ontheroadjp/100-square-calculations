import './styles/main.scss';
import { t } from './strings.js';
import { buildDrillCatalog, DRILL_FORMS } from './drillCatalog.js';
import { mountNavShell } from './navShell.js';
import { UNGRADED } from './drillPresets.js';

const API_BASE = 'http://127.0.0.1:5000';

mountNavShell();

async function renderAvailableForms() {
  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    const data = await response.json();
    activeRenderer = data.renderer;
  } catch {
    activeRenderer = 'reportlab';
  }

  const catalog = buildDrillCatalog(activeRenderer).filter((drill) => drill.grade !== UNGRADED);
  const availableForms = DRILL_FORMS.filter((form) => catalog.some((drill) => drill.forms.includes(form)));
  if (availableForms.length === 0) return;

  const grid = document.getElementById('formStartGrid');
  grid.innerHTML = availableForms
    .map((form) => `<a class="drill-start-card" href="catalog.html?forms=${form}">${t(`form_${form}`)}</a>`)
    .join('');
  document.getElementById('formSection').hidden = false;
}

renderAvailableForms();
