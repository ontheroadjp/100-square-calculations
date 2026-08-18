import { ICONS } from './icons.js';

export function pageHeaderHtml(title, description) {
  return `
    <header class="catalog-header">
        <div class="catalog-header-title">
            <a class="page-header-row" href="index.html">${ICONS.chevronLeft}<h1 class="catalog-heading">${title}</h1></a>
        </div>
        <p class="category-picker-heading catalog-header-sub-title">${description}</p>
    </header>
  `;
}
