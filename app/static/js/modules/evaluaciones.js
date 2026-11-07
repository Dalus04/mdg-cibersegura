/**
 * Módulo de Cuestionarios Formales de Evaluación
 * MDG Cibersegura - Municipalidad Distrital de Guadalupe
 *
 * Funcionalidades:
 * - Contador dinámico de preguntas respondidas y barra de avance accesible.
 * - Limpieza de advertencias de preguntas incompletas tras selección.
 * - Deshabilitación de botón y feedback accesible al calificar.
 */

/**
 * Actualiza el contador dinámico y la barra de avance de preguntas respondidas.
 * @param {HTMLFormElement} form
 */
export function actualizarProgresoEvaluacion(form) {
  if (!form) return;
  const inputs = form.querySelectorAll('input[type="radio"][name^="pregunta_"]');
  if (!inputs.length) return;

  const grupos = new Set();
  const gruposRespondidos = new Set();

  inputs.forEach((i) => {
    grupos.add(i.name);
    if (i.checked) {
      gruposRespondidos.add(i.name);
    }
  });

  const total = grupos.size;
  const respondidas = gruposRespondidos.size;

  const contadorEl = document.getElementById('contador-respondidas');
  if (contadorEl) {
    contadorEl.textContent = respondidas;
  }

  const rellenoEl = document.getElementById('barra-progreso-relleno');
  if (rellenoEl) {
    const porcentaje = total > 0 ? Math.round((respondidas / total) * 100) : 0;
    rellenoEl.style.width = `${porcentaje}%`;
  }

  const barraAvance = form.querySelector('.barra-avance-eval');
  if (barraAvance) {
    barraAvance.setAttribute('aria-valuenow', respondidas);
  }
}

/**
 * Inicializa el comportamiento del cuestionario formal de evaluación.
 */
export function initEvaluaciones() {
  const form = document.getElementById('form-cuestionario-evaluacion');
  if (!form) return;

  actualizarProgresoEvaluacion(form);

  const inputs = form.querySelectorAll('input[type="radio"][name^="pregunta_"]');
  inputs.forEach((input) => {
    input.addEventListener('change', () => {
      // Remover estado de pregunta incompleta si existía
      const fieldset = input.closest('.tarjeta-pregunta-evaluacion');
      if (fieldset) {
        fieldset.classList.remove('pregunta-incompleta');
        const aviso = fieldset.querySelector('.aviso-pregunta-requerida');
        if (aviso) aviso.remove();
      }

      // Actualizar contador y barra de avance
      actualizarProgresoEvaluacion(form);
    });
  });

  form.addEventListener('submit', () => {
    const btn = document.getElementById('btn-enviar-evaluacion');
    if (btn && !btn.disabled) {
      setTimeout(() => {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.textContent = 'Calificando evaluación... ⏳';
      }, 10);
    }
  });
}

