import './styles/main.scss';
import { t } from './strings.js';
import { buildDrillCatalog } from './drillCatalog.js';
import { mountPresetDetail } from './presetDetail.js';
import { mountNavShell } from './navShell.js';

const API_BASE = 'http://127.0.0.1:5000';

mountNavShell();

async function findPreset() {
  const params = new URLSearchParams(location.search);
  const grade = params.get('grade');
  const drillId = params.get('drillId');
  const format = params.get('format');

  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    activeRenderer = (await response.json()).renderer;
  } catch {
    activeRenderer = 'reportlab';
  }

  const catalog = buildDrillCatalog(activeRenderer);
  const drill = catalog.find((candidate) => candidate.id === drillId);
  const preset = drill?.presets[format];
  return preset ? { grade, preset } : null;
}

const container = document.getElementById('detail');
const found = await findPreset();
if (found) {
  mountPresetDetail(container, { ...found, onBack: () => history.back() });
} else {
  container.innerHTML = `<p class="drill-empty-state">${t('no_drills_found')}</p><a class="back-button" href="index.html">${t('back')}</a>`;
}
