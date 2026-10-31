/**
 * Módulo de Accesibilidad (WCAG 2.2 Nivel AA)
 * MDG Cibersegura - Municipalidad Distrital de Guadalupe
 *
 * Funcionalidades:
 * - Corrección de navegación por teclado para el enlace de salto (skip link).
 * - Mejora de accesibilidad en grupos de opciones y cuestionarios de radio.
 * - Soporte para anuncios dinámicos a lectores de pantalla (ARIA Live).
 */

/**
 * Anuncia un mensaje a tecnologías de asistencia mediante una región ARIA live.
 * @param {string} mensaje - Texto descriptivo para lectores de pantalla.
 * @param {'polite'|'assertive'} prioridad - Prioridad de interrupción verbal.
 */
export function anunciar(mensaje, prioridad = 'polite') {
  let anunciador = document.getElementById('mdg-anunciador-aria');
  if (!anunciador) {
    anunciador = document.createElement('div');
    anunciador.id = 'mdg-anunciador-aria';
    anunciador.className = 'sr-only';
    anunciador.setAttribute('aria-live', prioridad);
    anunciador.setAttribute('aria-atomic', 'true');
    document.body.appendChild(anunciador);
  } else {
    anunciador.setAttribute('aria-live', prioridad);
  }

  // Vaciar y asignar para asegurar lectura consecutiva
  anunciador.textContent = '';
  setTimeout(() => {
    anunciador.textContent = mensaje;
  }, 50);
}

/**
 * Inicializa el manejo del enlace accesible para saltar al contenido principal.
 */
function initSkipLink() {
  const skipLink = document.querySelector('.saltar-contenido');
  if (!skipLink) return;

  skipLink.addEventListener('click', (event) => {
    const destinoId = skipLink.getAttribute('href')?.replace('#', '');
    const mainTarget = document.getElementById(destinoId);
    if (mainTarget) {
      if (!mainTarget.hasAttribute('tabindex')) {
        mainTarget.setAttribute('tabindex', '-1');
        mainTarget.addEventListener('blur', () => {
          mainTarget.removeAttribute('tabindex');
        }, { once: true });
      }
      mainTarget.focus({ preventScroll: false });
    }
  });
}

/**
 * Inicializa la navegación por teclado mejorada en tarjetas de selección (radio buttons).
 */
function initRadioCards() {
  const cards = document.querySelectorAll('.tarjeta-opcion-decision, .tarjeta-alternativa-item');

  cards.forEach((card) => {
    const radio = card.querySelector('input[type="radio"]');
    if (!radio) return;

    // Permitir activar con la tarjeta completa
    card.addEventListener('click', (e) => {
      if (e.target !== radio) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        radio.focus();
      }
    });

    // Accesibilidad con teclado: Enter o Espacio en la tarjeta
    card.addEventListener('keydown', (e) => {
      if ((e.key === ' ' || e.key === 'Enter') && e.target === card) {
        e.preventDefault();
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        radio.focus();
      }
    });
  });
}

/**
 * Inicializa el módulo de accesibilidad.
 */
export function initAccesibilidad() {
  initSkipLink();
  initRadioCards();
}
