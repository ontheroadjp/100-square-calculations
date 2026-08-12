import './styles/main.scss';
import { mountCustomGenerator } from './customGenerator.js';

const API_BASE = 'http://127.0.0.1:5000';

async function mount() {
  let activeRenderer = 'reportlab';
  try {
    const response = await fetch(`${API_BASE}/renderer-info`);
    activeRenderer = (await response.json()).renderer;
  } catch {
    activeRenderer = 'reportlab';
  }
  mountCustomGenerator(document.getElementById('generator'), { supportsVertical: activeRenderer === 'latex' });
}

mount();
