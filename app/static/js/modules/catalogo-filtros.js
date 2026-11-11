/**
 * Filtrado interactivo del catálogo curricular (/temas)
 * MDG Cibersegura - Soporte WCAG 2.2 AA (aria-pressed, aria-live).
 */

export function initCatalogoFiltros() {
  const lista = document.getElementById('lista-fichas-curriculares');
  if (!lista) return;

  const fichas = Array.from(lista.querySelectorAll('.ficha-curricular'));
  const botonesEje = Array.from(document.querySelectorAll('[data-filtro-eje]'));
  const botonesEstado = Array.from(document.querySelectorAll('[data-filtro-estado]'));
  const botonesModalidad = Array.from(document.querySelectorAll('[data-filtro-modalidad]'));
  const contador = document.getElementById('catalogo-contador-resultados');
  const mensajeVacio = document.getElementById('catalogo-sin-resultados');

  let ejeActivo = 'todos';
  let estadoActivo = 'todos';
  let modalidadActiva = 'todos';

  function actualizarVista() {
    let visibles = 0;

    fichas.forEach((ficha) => {
      const coincideEje = ejeActivo === 'todos' || ficha.dataset.eje === ejeActivo;
      const coincideEstado =
        estadoActivo === 'todos' || ficha.dataset.estadoFiltro === estadoActivo;
      const coincideModalidad =
        modalidadActiva === 'todos' ||
        (modalidadActiva === 'practica' && ficha.dataset.practica === 'si') ||
        (modalidadActiva === 'evaluacion' && ficha.dataset.evaluacion === 'si');

      const mostrar = coincideEje && coincideEstado && coincideModalidad;
      ficha.hidden = !mostrar;
      if (mostrar) visibles += 1;
    });

    if (contador) {
      contador.textContent = `Mostrando ${visibles} de ${fichas.length} módulos formativos`;
    }

    if (mensajeVacio) {
      mensajeVacio.hidden = visibles > 0;
    }
  }

  botonesEje.forEach((btn) => {
    btn.addEventListener('click', () => {
      ejeActivo = btn.dataset.filtroEje || 'todos';
      botonesEje.forEach((b) => {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      actualizarVista();
    });
  });

  botonesEstado.forEach((btn) => {
    btn.addEventListener('click', () => {
      estadoActivo = btn.dataset.filtroEstado || 'todos';
      botonesEstado.forEach((b) => {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      actualizarVista();
    });
  });

  botonesModalidad.forEach((btn) => {
    btn.addEventListener('click', () => {
      modalidadActiva = btn.dataset.filtroModalidad || 'todos';
      botonesModalidad.forEach((b) => {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      actualizarVista();
    });
  });
}
