import './styles/main.scss';
import { t } from './strings.js';
import { ICONS } from './icons.js';
import { mountNavShell } from './navShell.js';
import { mountPcMakeFlow } from './pcMakeFlow.js';

mountNavShell();
mountPcMakeFlow(document.getElementById('pcMakeFlow'));

// Matches the wireframe's top-screen brand header (docs/uiux/wireframe_v1.png
// "① トップ"): icon + app name, same ICONS.brand/nav_brand pair used by
// navShell.js's sidebar. Only visible on mobile — _pcMakeFlow.scss hides
// .app-header at the desktop breakpoint in favor of the 4-column layout's
// own breadcrumb.
document.getElementById('appHeader').innerHTML = `
  <h1 class="app-header-brand">${ICONS.brand}<span>${t('nav_brand')}</span></h1>
`;

// Matches the wireframe's grade-card avatar icon (docs/uiux/wireframe_v1.png
// "① トップ"). Injected via JS rather than duplicated inline six times in
// index.html, keeping icons.js the single source of truth.
document.querySelectorAll('.grade-picker-card').forEach((card) => {
  card.insertAdjacentHTML('afterbegin', `<span class="grade-picker-avatar" aria-hidden="true">${ICONS.face}</span>`);
});
