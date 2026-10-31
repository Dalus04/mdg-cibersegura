/**
 * Punto de entrada JavaScript (ES Module)
 * MDG Cibersegura - Municipalidad Distrital de Guadalupe
 *
 * Arquitectura modular con Progressive Enhancement y soporte WCAG 2.2 AA.
 */

import { initAccesibilidad } from './modules/accesibilidad.js';
import { initSimulador } from './modules/simulador.js';

document.addEventListener('DOMContentLoaded', () => {
  // Inicialización de accesibilidad global
  initAccesibilidad();

  // Inicialización de simulaciones y actividades interactivas
  initSimulador();
});
