/**
 * Módulo de Simulador y Actividades Prácticas
 * MDG Cibersegura - Municipalidad Distrital de Guadalupe
 *
 * Funcionalidades:
 * - Protección contra navegación en enlaces simulados de phishing.
 * - Inspección interactiva de URLs sospechosas con retroalimentación visual inmediata.
 * - Realce dinámico de opciones seleccionadas en talleres y simulaciones de decisión.
 */

import { anunciar } from './accesibilidad.js';

/**
 * Muestra una alerta flotante accesible de inspección segura.
 * @param {string} mensaje 
 */
function mostrarAvisoSeguridad(mensaje) {
  let avisoExistente = document.getElementById('aviso-simulacion-temporal');
  if (!avisoExistente) {
    avisoExistente = document.createElement('div');
    avisoExistente.id = 'aviso-simulacion-temporal';
    avisoExistente.className = 'aviso-simulacion-alerta';
    avisoExistente.setAttribute('aria-hidden', 'true');
    document.body.appendChild(avisoExistente);
  }

  avisoExistente.innerHTML = `
    <span class="texto-aviso-simulacion">${mensaje}</span>
    <button type="button" class="btn-cerrar-aviso" aria-label="Cerrar aviso de simulación">×</button>
  `;

  const btnCerrar = avisoExistente.querySelector('.btn-cerrar-aviso');
  if (btnCerrar) {
    btnCerrar.addEventListener('click', () => {
      clearTimeout(window.__mdgAvisoTimer);
      avisoExistente.remove();
    });
  }

  // Anuncio para tecnologías de asistencia vía anunciador centralizado
  anunciar(mensaje, 'assertive');

  clearTimeout(window.__mdgAvisoTimer);
  window.__mdgAvisoTimer = setTimeout(() => {
    if (avisoExistente && avisoExistente.parentNode) {
      avisoExistente.remove();
    }
  }, 4500);
}

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
 * Inicializa la confirmación visual de alternativas seleccionadas en actividades y cuestionarios.
 */
function initSeleccionOpciones() {
  const radioInputs = document.querySelectorAll(
    'input[type="radio"][name="opcion_id"], input[type="radio"][name="alternativa_id"], input[type="radio"][name^="pregunta_"]'
  );
  if (!radioInputs.length) return;

  radioInputs.forEach((input) => {
    input.addEventListener('change', () => {
      const form = input.closest('form') || document;
      const name = input.getAttribute('name');
      if (name) {
        const inputsMismoGrupo = form.querySelectorAll(`input[type="radio"][name="${name}"]`);
        inputsMismoGrupo.forEach((i) => {
          const c = i.closest('.tarjeta-opcion-decision, .tarjeta-alternativa-item');
          if (c) c.classList.remove('opcion-activa');
        });
      }

      // Agregar clase activa a la tarjeta seleccionada (soporte visual para navegadores sin :has)
      const parentCard = input.closest('.tarjeta-opcion-decision, .tarjeta-alternativa-item');
      if (parentCard) {
        parentCard.classList.add('opcion-activa');
      }
    });
  });
}

/**
 * Inicializa las mejoras interactivas del simulador de ciberseguridad.
 */
export function initSimulador() {
  initInspeccionEnlaces();
  initSeleccionOpciones();
}
