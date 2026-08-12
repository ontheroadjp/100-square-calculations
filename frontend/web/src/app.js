import { t } from './strings.js';
import { mountGradeDrills } from './gradeDrills.js';

export function renderApp(root) {
  root.innerHTML = `
    <div class="app-container">
      <header class="app-header">
        <h1>${t('app_title')}</h1>
      </header>
      <main class="main-content" id="main-content"></main>
    </div>
  `;
  mountGradeDrills(document.getElementById('main-content'));
}
