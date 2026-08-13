import { t } from './strings.js';

const ICONS = {
  home: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>',
  create: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>',
  history: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M4 12h16M4 18h10"/></svg>',
  favorite: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17.3l-6.2 3.6 1.6-7L2 9.2l7.1-.6L12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7z"/></svg>',
  mypage: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
};

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
    <a class="sidebar-brand" href="index.html">${ICONS.create}<span>${t('nav_brand')}</span></a>
    ${SIDEBAR_ITEMS.map((item) => navItemHtml(item, 'sidebar-item')).join('')}
  `;

  document.body.prepend(sidebar);
  document.body.append(bottomBar);
}
