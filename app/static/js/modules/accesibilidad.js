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
 * Inicializa los botones de alternancia para visualizar/ocultar contraseñas.
 */
function initPasswordToggles() {
  const toggles = document.querySelectorAll('.boton-toggle-password');
  toggles.forEach((button) => {
    button.addEventListener('click', () => {
      const wrap = button.closest('.campo-password-wrap');
      if (!wrap) return;
      const input = wrap.querySelector('input');
      if (!input) return;

      const isPressed = button.getAttribute('aria-pressed') === 'true';
      if (isPressed) {
        input.type = 'password';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-label', 'Mostrar contraseña');
        button.setAttribute('title', 'Mostrar contraseña');
        anunciar('Contraseña oculta', 'polite');
      } else {
        input.type = 'text';
        button.setAttribute('aria-pressed', 'true');
        button.setAttribute('aria-label', 'Ocultar contraseña');
        button.setAttribute('title', 'Ocultar contraseña');
        anunciar('Contraseña visible', 'polite');
      }
      input.focus();
    });
  });
}

/**
 * Gestiona el foco accesible hacia el primer campo con error al cargar la página.
 */
function initErrorFocusManagement() {
  const firstInvalid = document.querySelector('.campo input[aria-invalid="true"]');
  if (firstInvalid) {
    firstInvalid.focus();
    return;
  }

  const firstErrorAlert = document.querySelector('.mensaje-error');
  if (firstErrorAlert && !firstErrorAlert.hasAttribute('tabindex')) {
    firstErrorAlert.setAttribute('tabindex', '-1');
    firstErrorAlert.focus();
  }
}

/**
 * Previene el doble envío de formularios y proporciona estado de carga accesible.
 */
function initFormSubmitProtection() {
  const forms = document.querySelectorAll('.tarjeta-formulario form');
  forms.forEach((form) => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
      if (!submitBtn) return;

      if (!form.checkValidity()) return;

      if (form.dataset.submitting === 'true') {
        e.preventDefault();
        return;
      }

      form.dataset.submitting = 'true';

      // Modificar texto visual accesible
      if (submitBtn.tagName === 'INPUT') {
        submitBtn.dataset.originalValue = submitBtn.value;
        submitBtn.value = 'Procesando...';
      } else {
        submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.textContent = 'Procesando...';
      }

      // Deshabilitar tras un micro-tick para permitir que el formulario capture el evento
      setTimeout(() => {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.75';
        submitBtn.style.cursor = 'wait';
      }, 0);
    });
  });

  // Restaurar estado si el usuario regresa con el botón Atrás (bfcache)
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('.tarjeta-formulario form').forEach((form) => {
      delete form.dataset.submitting;
      const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '';
        submitBtn.style.cursor = '';
        if (submitBtn.dataset.originalValue) {
          submitBtn.value = submitBtn.dataset.originalValue;
        } else if (submitBtn.dataset.originalHtml) {
          submitBtn.innerHTML = submitBtn.dataset.originalHtml;
        }
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
  initPasswordToggles();
  initErrorFocusManagement();
  initFormSubmitProtection();
}
