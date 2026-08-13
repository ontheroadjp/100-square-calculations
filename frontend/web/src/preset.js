import './styles/main.scss';
import { t } from './strings.js';
import { GRADES, UNGRADED, presetsByGrade } from './drillPresets.js';
import { mountPresetDetail } from './presetDetail.js';
import { mountNavShell } from './navShell.js';

const API_BASE = 'http://127.0.0.1:5000';

mountNavShell();

function canUseItem(item, renderer) {
  return !item.latexOnly || renderer === 'latex';
}

// Item ids are unique across the whole data model (drillPresets.test.js),
// so a plain id search doesn't need the URL's grade to disambiguate.
function findItemById(drillId, renderer) {
  for (const gradeKey of [...GRADES, UNGRADED]) {
    for (const items of Object.values(presetsByGrade[gradeKey])) {
      const item = items.find((candidate) => candidate.id === drillId);
      if (item && canUseItem(item, renderer)) return item;
    }
  }
  return null;
}

async function findPreset() {
  const params = new URLSearchParams(location.search);
  const grade = params.get('grade');
  const drillId = params.get('drillId');

  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    activeRenderer = (await response.json()).renderer;
  } catch {
    activeRenderer = 'reportlab';
  }

  const item = findItemById(drillId, activeRenderer);
  return item ? { grade, item } : null;
}

const container = document.getElementById('detail');
const found = await findPreset();
if (found) {
  mountPresetDetail(container, { ...found, onBack: () => history.back() });
} else {
  container.innerHTML = `<p class="drill-empty-state">${t('no_drills_found')}</p><a class="back-button" href="index.html">${t('back')}</a>`;
}
