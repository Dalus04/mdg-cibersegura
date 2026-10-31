/**
 * Módulo de Simulador y Actividades Prácticas
 * MDG Cibersegura - Municipalidad Distrital de Guadalupe
 *
 * Funcionalidades:
 * - Protección contra clics no deseados en enlaces simulados de phishing.
 * - Inspección interactiva de URLs sospechosas con retroalimentación visual inmediata.
 * - Realce dinámico de opciones seleccionadas en talleres de decisión.
 */

import { anunciar } from './accesibilidad.js';

/**
 * Inicializa la inspección de enlaces sospechosos dentro del simulador de correo.
 */
function initInspeccionEnlaces() {
  const correoSimulado = document.querySelector('.cliente-correo-simulado');
  if (!correoSimulado) return;

  const enlacesSospechosos = correoSimulado.querySelectorAll('a, .inspeccion-enlace-alerta code');

  enlacesSospechosos.forEach((el) => {
    // Evitar navegación real si es un enlace simulado
    if (el.tagName.toLowerCase() === 'a') {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        mostrarAvisoSeguridad('🛡️ Enlace simulado: Recuerde no hacer clic en enlaces no verificados en correos reales.');
      });
    }

    // Efecto de inspección interactiva
    el.setAttribute('title', '🔍 Inspección de URL sospechosa (Simulación segura)');
    el.style.cursor = 'help';
  });
}

/**
 * Muestra una alerta temporal de inspección segura.
 * @param {string} mensaje 
 */
function mostrarAvisoSeguridad(mensaje) {
  let avisoExistente = document.getElementById('aviso-simulacion-temporal');
  if (!avisoExistente) {
    avisoExistente = document.createElement('div');
    avisoExistente.id = 'aviso-simulacion-temporal';
    avisoExistente.setAttribute('role', 'alert');
    avisoExistente.style.cssText = `
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: #0f2a4a;
      color: #ffffff;
      padding: 0.85rem 1.25rem;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
      font-size: 0.9rem;
      font-weight: 600;
      z-index: 1000;
      max-width: 24rem;
      animation: fadeIn 0.2s ease;
    `;
    document.body.appendChild(avisoExistente);
  }

  avisoExistente.textContent = mensaje;
  anunciar(mensaje, 'assertive');

  clearTimeout(window.__mdgAvisoTimer);
  window.__mdgAvisoTimer = setTimeout(() => {
    if (avisoExistente && avisoExistente.parentNode) {
      avisoExistente.remove();
    }
  }, 4500);
}

/**
 * Inicializa la confirmación visual de alternativas seleccionadas.
 */
function initSeleccionOpciones() {
  const radioInputs = document.querySelectorAll('input[type="radio"][name="alternativa_id"]');
  if (!radioInputs.length) return;

  radioInputs.forEach((input) => {
    input.addEventListener('change', () => {
      // Remover clase seleccionada de todas
      const tarjetas = document.querySelectorAll('.tarjeta-opcion-decision, .tarjeta-alternativa-item');
      tarjetas.forEach((t) => t.classList.remove('opcion-activa'));

      // Agregar a la tarjeta seleccionada
      const parentCard = input.closest('.tarjeta-opcion-decision, .tarjeta-alternativa-item');
      if (parentCard) {
        parentCard.classList.add('opcion-activa');
        const labelText = parentCard.innerText.trim().slice(0, 60);
        anunciar(`Opción seleccionada: ${labelText}`);
      }
    });
  });
}

/**
 * Inicializa las mejoras interactivas de las actividades.
 */
export function initSimulador() {
  initInspeccionEnlaces();
  initSeleccionOpciones();
}
