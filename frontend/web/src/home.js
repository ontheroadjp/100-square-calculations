import './styles/main.scss';
import { mountNavShell } from './navShell.js';
import { mountPcMakeFlow } from './pcMakeFlow.js';

mountNavShell();
mountPcMakeFlow(document.getElementById('pcMakeFlow'));
