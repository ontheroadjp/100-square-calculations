import { t } from './strings.js';
import { ICONS } from './icons.js';

// "ホーム" and "作る" both link to index.html (the top/grade-selection
// screen). Only "作る" renders active: the wireframe's separate "repeater
// home" screen doesn't exist yet, so every current page (index/catalog/
// preset) belongs to the "作る" main flow.
const MOBILE_TABS = [
  { key: 'home', labelKey: 'nav_home', href: 'index.html' },
  { key: 'create', labelKey: 'nav_create', href: 'index.html', active: true },
  { key: 'history', labelKey: 'nav_history' },
  { key: 'mypage', labelKey: 'nav_mypage' },
];

const SIDEBAR_ITEMS = [
  { key: 'home', labelKey: 'nav_home', href: 'index.html' },
  { key: 'create', labelKey: 'nav_create', href: 'index.html', active: true },
  { key: 'history', labelKey: 'nav_history' },
  { key: 'favorite', labelKey: 'nav_favorites' },
  { key: 'mypage', labelKey: 'nav_mypage' },
];

function navItemHtml(item, extraClass) {
  const classes = ['nav-item', extraClass, item.active ? 'active' : ''].filter(Boolean).join(' ');
  const icon = ICONS[item.key];
  const label = t(item.labelKey);
  if (item.href) {
    return `<a class="${classes}" href="${item.href}">${icon}<span>${label}</span></a>`;
  }
  return `<button type="button" class="${classes}" disabled>${icon}<span>${label}</span></button>`;
}

export function mountNavShell() {
  const bottomBar = document.createElement('nav');
  bottomBar.className = 'bottom-tab-bar';
  bottomBar.setAttribute('aria-label', t('nav_mobile_label'));
  bottomBar.innerHTML = MOBILE_TABS.map((item) => navItemHtml(item, 'tab-item')).join('');

  const sidebar = document.createElement('nav');
  sidebar.className = 'pc-sidebar';
  sidebar.setAttribute('aria-label', t('nav_pc_label'));
  sidebar.innerHTML = `
    <a class="sidebar-brand" href="index.html">${ICONS.brand}<span>${t('nav_brand')}</span></a>
    ${SIDEBAR_ITEMS.map((item) => navItemHtml(item, 'sidebar-item')).join('')}
  `;

  document.body.prepend(sidebar);
  document.body.append(bottomBar);
}
