// Gestión Avanzada de Menús por Modalidad - Módulo de Nutrición
let programaActual = null;
let municipioActual = null;
let modalidadesData = [];
let menusData = {};
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    // Si hay municipio preseleccionado, cargar programas
    if (typeof MUNICIPIO_ACTUAL !== 'undefined' && MUNICIPIO_ACTUAL) {
        cargarProgramasPorMunicipio(MUNICIPIO_ACTUAL);
    }
});
function inicializarEventos() {
    const filtroMunicipio = document.getElementById('filtroMunicipio');
    if (!filtroMunicipio) {
        return;
    }
    filtroMunicipio.addEventListener('change', function() {
        const municipioId = this.value;
        municipioActual = municipioId;
        if (municipioId) {
            cargarProgramasPorMunicipio(municipioId);
        } else {
            resetearFiltros();
        }
    });
    const filtroPrograma = document.getElementById('filtroPrograma');
    if (filtroPrograma) {
        filtroPrograma.addEventListener('change', function() {
            const programaId = this.value;
            document.getElementById('btnAplicarFiltros').disabled = !programaId;
        });
    }
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', function() {
            const programaId = document.getElementById('filtroPrograma').value;
            if (programaId) {
                cargarModalidadesPorPrograma(programaId);
            }
        });
    }
}
async function cargarProgramasPorMunicipio(municipioId) {
    try {
        const url = `/nutricion/api/programas-por-municipio/?municipio_id=${municipioId}`;
        const response = await fetch(url);
        const data = await response.json();
        const selectPrograma = document.getElementById('filtroPrograma');
        if (!selectPrograma) {
            return;
        }
        selectPrograma.innerHTML = '<option value="">Seleccione un programa...</option>';
        if (data.programas && data.programas.length > 0) {
            data.programas.forEach(programa => {
                const option = document.createElement('option');
                option.value = programa.id;
                option.textContent = `${programa.programa} (${programa.contrato})`;
                selectPrograma.appendChild(option);
            });
            selectPrograma.disabled = false;
            // Si solo hay un programa, seleccionarlo automáticamente
            if (data.programas.length === 1) {
                selectPrograma.value = data.programas[0].id;
                document.getElementById('btnAplicarFiltros').disabled = false;
            }
        } else {
            selectPrograma.innerHTML = '<option value="">No hay programas activos en este municipio</option>';
            selectPrograma.disabled = true;
        }
    } catch (error) {
        console.error('Error al cargar programas:', error);
        alert('Error al cargar programas del municipio');
    }
}
async function cargarModalidadesPorPrograma(programaId) {
    try {
        const url = `/nutricion/api/modalidades-por-programa/?programa_id=${programaId}`;
        const response = await fetch(url);
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }
        programaActual = data.programa;
        modalidadesData = data.modalidades;
        mostrarInfoPrograma(data.programa);
        document.getElementById('mensajeInicial').style.display = 'none';
        await cargarMenusExistentes(programaId);
        generarAcordeones(data.modalidades);
    } catch (error) {
        console.error('Error al cargar modalidades:', error);
        alert('Error al cargar modalidades del programa');
    }
}
async function cargarMenusExistentes(programaId) {
    try {
        const response = await fetch(`/nutricion/api/menus/?programa_id=${programaId}`);
        const data = await response.json();
        // Agrupar menús por modalidad
        menusData = {};
        if (data.menus) {
            data.menus.forEach(menu => {
                const modalidadId = menu.id_modalidad__id_modalidades;
                if (!menusData[modalidadId]) {
                    menusData[modalidadId] = [];
                }
                menusData[modalidadId].push(menu);
            });
            // Ordenar menús numéricamente dentro de cada modalidad
            Object.keys(menusData).forEach(modalidadId => {
                menusData[modalidadId].sort((a, b) => {
                    const numA = parseInt(a.menu) || 0;
                    const numB = parseInt(b.menu) || 0;
                    return numA - numB;
                });
            });
        }
    } catch (error) {
        console.error('Error al cargar menús:', error);
    }
}
function mostrarInfoPrograma(programa) {
    const container = document.getElementById('infoProgramaContainer');
    document.getElementById('infoProgramaNombre').querySelector('span').textContent = programa.nombre;
    document.getElementById('infoProgramaContrato').querySelector('span').textContent = programa.contrato;
    const municipioSelect = document.getElementById('filtroMunicipio');
    const municipioNombre = municipioSelect.options[municipioSelect.selectedIndex].text;
    document.getElementById('infoProgramaMunicipio').querySelector('span').textContent = municipioNombre;
    container.style.display = 'block';
}
function generarAcordeones(modalidades) {
    const container = document.getElementById('modalidadesContainer');
    container.innerHTML = '';
    modalidades.forEach(modalidad => {
        const accordion = crearAcordeon(modalidad);
        container.appendChild(accordion);
    });
}
function crearAcordeon(modalidad) {
    const modalidadId = modalidad.id_modalidades;
    const menusModalidad = menusData[modalidadId] || [];
    const tieneMenus = menusModalidad.length > 0;
    const accordionDiv = document.createElement('div');
    accordionDiv.className = 'accordion';
    // Crear header
    const header = document.createElement('div');
    header.className = 'accordion-header';
    header.onclick = function() { toggleAccordion(this); };
    header.innerHTML = `
        <div>
            <strong>${modalidad.modalidad}</strong>
            <span class="preparacion-badge">${menusModalidad.length} / 20 menús</span>
        </div>
        <div>
            ${!tieneMenus ? `<button class="btn-generar-auto" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                <i class="fas fa-magic"></i> Generar 20 Menús
            </button>` : ''}
            <i class="fas fa-chevron-down"></i>
        </div>
    `;
    // Agregar event listener al botón si existe
    if (!tieneMenus) {
        setTimeout(() => {
            const btn = header.querySelector('.btn-generar-auto');
            if (btn) {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const modalidadId = this.getAttribute('data-modalidad-id');
                    const modalidadNombre = this.getAttribute('data-modalidad-nombre');
                    generarMenusAutomaticos(modalidadId, modalidadNombre);
                });
            }
        }, 0);
    }
    // Crear content
    const content = document.createElement('div');
    content.className = 'accordion-content';
    content.id = `content-${modalidadId}`;
    const grid = document.createElement('div');
    grid.className = 'menus-grid';
    grid.id = `grid-${modalidadId}`;
    if (tieneMenus) {
        grid.innerHTML = generarTarjetasMenus(menusModalidad);
    } else {
        grid.innerHTML = '<p style="padding: 20px;">Genere los menús para esta modalidad</p>';
    }
    content.appendChild(grid);
    accordionDiv.appendChild(header);
    accordionDiv.appendChild(content);
    return accordionDiv;
}
function generarTarjetasMenus(menus) {
    const tarjetasMenus = menus.map(menu => {
        // Detectar si es un menú especial (no es un número del 1-20)
        const esNumerico = !isNaN(menu.menu) && parseInt(menu.menu) >= 1 && parseInt(menu.menu) <= 20;
        const esEspecial = !esNumerico;
        const menuEscaped = String(menu.menu).replace(/'/g, "\\'");

        if (esEspecial) {
            // Tarjeta para menú especial existente
            return `
                <div class="menu-card menu-card-especial ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                    <div class="menu-numero-especial" style="font-size: 14px; margin-bottom: 8px;">
                        ${menu.menu}
                    </div>
                    <div class="menu-actions" style="flex-direction: column; gap: 5px;">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                            <i class="fas fa-utensils"></i> Preparaciones
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); abrirEditarMenuEspecial(${menu.id_menu}, '${menuEscaped}')">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); eliminarMenuEspecial(${menu.id_menu}, '${menuEscaped}')">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </div>
                </div>
            `;
        } else {
            // Tarjeta para menú numérico normal
            return `
                <div class="menu-card ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                    <div class="menu-numero">${menu.menu}</div>
                    <div class="menu-actions">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                            <i class="fas fa-utensils"></i> Preparaciones
                        </button>
                    </div>
                </div>
            `;
        }
    }).join('');

    // Agregar tarjeta para crear nuevo menú especial
    const modalidadId = menus.length > 0 ? menus[0].id_modalidad__id_modalidades : '';
    const tarjetaEspecial = `
        <div class="menu-card menu-card-especial" onclick="abrirModalMenuEspecial('${modalidadId}')">
            <div class="menu-numero-especial">
                <i class="fas fa-plus-circle"></i>
            </div>
            <div class="menu-label-especial">Crear Menú Especial</div>
        </div>
    `;

    return tarjetasMenus + tarjetaEspecial;
}
function toggleAccordion(header) {
    const content = header.nextElementSibling;
    const isActive = content.classList.contains('active');
    // Cerrar todos los acordeones
    document.querySelectorAll('.accordion-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.accordion-header').forEach(h => h.classList.remove('active'));
    // Abrir el actual si estaba cerrado
    if (!isActive) {
        content.classList.add('active');
        header.classList.add('active');
    }
}
async function generarMenusAutomaticos(modalidadId, modalidadNombre) {
    if (!confirm(`¿Generar automáticamente 20 menús para ${modalidadNombre}?`)) {
        return;
    }
    try {
        const response = await fetch('/nutricion/api/generar-menus-automaticos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                programa_id: programaActual.id,
                modalidad_id: modalidadId
            })
        });
        const data = await response.json();
        if (data.success) {
            alert(`✓ Se generaron ${data.menus_creados} menús exitosamente`);
            // Recargar la vista
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudieron generar los menús'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al generar menús automáticos');
    }
}
let menuActualId = null;
function abrirGestionPreparaciones(menuId, menuNumero) {
    menuActualId = menuId; // Guardar el ID del menú actual
    menuActualAnalisis = menuId; // Guardar para el análisis nutricional
    document.getElementById('menuNumeroModal').textContent = menuNumero;
    document.getElementById('modalPreparaciones').style.display = 'block';

    // Configurar el botón de agregar preparación
    const btnAgregar = document.getElementById('btnAgregarPreparacion');
    if (btnAgregar) {
        // Remover listeners anteriores
        btnAgregar.replaceWith(btnAgregar.cloneNode(true));
        const nuevoBtn = document.getElementById('btnAgregarPreparacion');
        nuevoBtn.addEventListener('click', function() {
            abrirModalNuevaPreparacion(menuId);
        });
    }
    // Cargar preparaciones del menú
    cargarPreparacionesMenu(menuId);
}
function abrirModalNuevaPreparacion(menuId) {
    document.getElementById('menuIdPrep').value = menuId;
    document.getElementById('nombrePreparacion').value = '';
    document.getElementById('modalNuevaPreparacion').style.display = 'block';
}
// Configurar el formulario de nueva preparación
document.addEventListener('DOMContentLoaded', function() {
    const formNuevaPrep = document.getElementById('formNuevaPreparacion');
    if (formNuevaPrep) {
        formNuevaPrep.addEventListener('submit', async function(e) {
            e.preventDefault();
            const menuId = document.getElementById('menuIdPrep').value;
            const nombrePrep = document.getElementById('nombrePreparacion').value.trim();
            if (!nombrePrep) {
                alert('Por favor ingrese un nombre para la preparación');
                return;
            }
            try {
                const response = await fetch('/nutricion/api/preparaciones/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        id_menu: menuId,
                        preparacion: nombrePrep
                    })
                });
                const data = await response.json();
                if (data.success || data.id_preparacion) {
                    alert(`✓ Preparación "${nombrePrep}" creada exitosamente`);
                    document.getElementById('modalNuevaPreparacion').style.display = 'none';
                    // Recargar la tabla de preparaciones
                    cargarPreparacionesMenu(menuId);
                } else {
                    alert('Error: ' + (data.error || 'No se pudo crear la preparación'));
                }
            } catch (error) {
                alert('Error al crear la preparación');
            }
        });
    }
});
async function cargarPreparacionesMenu(menuId) {
    try {
        const response = await fetch(`/nutricion/api/preparaciones/?menu_id=${menuId}`);
        const data = await response.json();
        const container = document.getElementById('listaPreparacionesAcordeon');
        container.innerHTML = '';
        if (data.preparaciones && data.preparaciones.length > 0) {
            // Cargar cada preparación con su cantidad de ingredientes
            for (const prep of data.preparaciones) {
                // Obtener cantidad de ingredientes
                const cantidadIngredientes = await obtenerCantidadIngredientes(prep.id_preparacion);
                prep.cantidad_ingredientes = cantidadIngredientes;

                const accordion = crearAcordeonPreparacion(prep, menuId);
                container.appendChild(accordion);
            }
        } else {
            container.innerHTML = '<div class="no-ingredientes"><i class="fas fa-info-circle"></i> No hay preparaciones asociadas a este menú</div>';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function obtenerCantidadIngredientes(preparacionId) {
    try {
        const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`);
        const data = await response.json();
        return data.ingredientes ? data.ingredientes.length : 0;
    } catch (error) {
        console.error('Error al obtener cantidad de ingredientes:', error);
        return 0;
    }
}
function crearAcordeonPreparacion(preparacion, menuId) {
    const accordionDiv = document.createElement('div');
    accordionDiv.className = 'preparacion-accordion';
    // Header del acordeón
    const header = document.createElement('div');
    header.className = 'preparacion-accordion-header';
    header.innerHTML = `
        <div class="preparacion-info">
            <div class="preparacion-nombre">${preparacion.preparacion}</div>
            <span class="ingredientes-badge">
                <i class="fas fa-cubes"></i> ${preparacion.cantidad_ingredientes || 0} ingredientes
            </span>
        </div>
        <div class="preparacion-actions">
            <button class="btn btn-icon btn-delete" title="Eliminar preparación">
                <i class="fas fa-trash"></i>
            </button>
            <i class="fas fa-chevron-down"></i>
        </div>
    `;
    // Event para toggle
    header.addEventListener('click', function(e) {
        if (!e.target.closest('.btn-delete')) {
            togglePreparacionAccordion(this);
        }
    });
    // Event para eliminar
    const btnDelete = header.querySelector('.btn-delete');
    btnDelete.addEventListener('click', function(e) {
        e.stopPropagation();
        eliminarPreparacion(preparacion.id_preparacion, menuId);
    });
    // Content del acordeón
    const content = document.createElement('div');
    content.className = 'preparacion-accordion-content';
    content.id = `prep-content-${preparacion.id_preparacion}`;
    const container = document.createElement('div');
    container.className = 'ingredientes-container';
    container.innerHTML = `
        <button class="btn-agregar-ingrediente" onclick="abrirAgregarIngrediente(${preparacion.id_preparacion})">
            <i class="fas fa-plus"></i> Agregar Ingrediente
        </button>
        <div id="ingredientes-${preparacion.id_preparacion}" style="margin-top: 15px;">
            <div class="no-ingredientes">Haz clic para cargar ingredientes</div>
        </div>
    `;
    content.appendChild(container);
    accordionDiv.appendChild(header);
    accordionDiv.appendChild(content);
    return accordionDiv;
}
function togglePreparacionAccordion(header) {
    const content = header.nextElementSibling;
    const isActive = content.classList.contains('active');
    // Cerrar todos los acordeones
    document.querySelectorAll('.preparacion-accordion-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.preparacion-accordion-header').forEach(h => h.classList.remove('active'));
    // Abrir el actual si estaba cerrado
    if (!isActive) {
        content.classList.add('active');
        header.classList.add('active');
        // Cargar ingredientes si no están cargados
        const prepId = content.id.replace('prep-content-', '');
        const ingredientesDiv = document.getElementById(`ingredientes-${prepId}`);
        if (ingredientesDiv && ingredientesDiv.querySelector('.no-ingredientes')) {
            cargarIngredientesPreparacion(prepId);
        }
    }
}
async function cargarIngredientesPreparacion(preparacionId) {
    try {
        const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`);
        const data = await response.json();
        const container = document.getElementById(`ingredientes-${preparacionId}`);
        if (data.ingredientes && data.ingredientes.length > 0) {
            container.innerHTML = data.ingredientes.map(ing => `
                <div class="ingrediente-item">
                    <div class="ingrediente-info">
                        <div class="ingrediente-nombre">
                            <i class="fas fa-carrot"></i> ${ing.id_ingrediente_siesa__id_ingrediente_siesa} - ${ing.id_ingrediente_siesa__nombre_ingrediente}
                        </div>
                    </div>
                    <div class="ingrediente-acciones">
                        <button class="btn-icon btn-delete" onclick="eliminarIngrediente(${preparacionId}, '${ing.id_ingrediente_siesa__id_ingrediente_siesa}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="no-ingredientes"><i class="fas fa-info-circle"></i> No hay ingredientes agregados</div>';
        }
    } catch (error) {
        console.error('Error al cargar ingredientes:', error);
    }
}
async function eliminarPreparacion(preparacionId, menuId) {
    if (!confirm('¿Está seguro de eliminar esta preparación?')) {
        return;
    }
    try {
        const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        if (data.success) {
            alert('✓ Preparación eliminada exitosamente');
            cargarPreparacionesMenu(menuId);
        } else {
            alert('Error: ' + (data.error || 'No se pudo eliminar'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar la preparación');
    }
}
let ingredientesSiesa = []; // Cache de ingredientes
async function abrirAgregarIngrediente(preparacionId) {
    document.getElementById('preparacionIdIngredientes').value = preparacionId;
    // Limpiar tabla
    document.getElementById('tbodyIngredientes').innerHTML = '';
    // Cargar ingredientes disponibles si no están cargados
    if (ingredientesSiesa.length === 0) {
        await cargarIngredientesSiesa();
    }
    // Agregar primera fila
    agregarFilaIngrediente();
    // Mostrar modal
    document.getElementById('modalAgregarIngredientes').style.display = 'block';
}
async function cargarIngredientesSiesa() {
    try {
        const response = await fetch('/nutricion/api/ingredientes/');
        const data = await response.json();
        if (data.ingredientes) {
            ingredientesSiesa = data.ingredientes;
        }
    } catch (error) {
        alert('Error al cargar lista de ingredientes');
    }
}
function agregarFilaIngrediente() {
    const tbody = document.getElementById('tbodyIngredientes');
    const filaIndex = tbody.children.length;
    const tr = document.createElement('tr');
    tr.className = 'fila-ingrediente';
    tr.id = `fila-ing-${filaIndex}`;
    // Select de ingredientes
    const optionsHTML = '<option value="">Seleccione un ingrediente...</option>' +
        ingredientesSiesa.map(ing => `<option value="${ing.id_ingrediente_siesa}">${ing.id_ingrediente_siesa} - ${ing.nombre_ingrediente}</option>`).join('');
    tr.innerHTML = `
        <td>
            <select class="select-ingrediente" id="ingrediente-${filaIndex}" required>
                ${optionsHTML}
            </select>
        </td>
        <td style="text-align: center;">
            <button type="button" class="btn-eliminar-fila" onclick="eliminarFilaIngrediente(${filaIndex})">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);

    // Inicializar Select2 en el select recién agregado
    $(`#ingrediente-${filaIndex}`).select2({
        placeholder: 'Buscar ingrediente...',
        allowClear: true,
        language: {
            noResults: function() {
                return "No se encontraron ingredientes";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownParent: $('#modalAgregarIngredientes')
    });
}
function eliminarFilaIngrediente(index) {
    // Destruir la instancia de Select2 antes de eliminar la fila
    $(`#ingrediente-${index}`).select2('destroy');

    const fila = document.getElementById(`fila-ing-${index}`);
    if (fila) {
        fila.remove();
    }
}
async function guardarIngredientes() {
    const preparacionId = document.getElementById('preparacionIdIngredientes').value;
    const tbody = document.getElementById('tbodyIngredientes');
    const filas = tbody.querySelectorAll('.fila-ingrediente');

    if (filas.length === 0) {
        alert('Agregue al menos un ingrediente');
        return;
    }

    const ingredientes = [];
    let hayErrores = false;

    filas.forEach((fila, index) => {
        const ingredienteId = document.getElementById(`ingrediente-${index}`)?.value;

        if (!ingredienteId) {
            hayErrores = true;
            return;
        }

        ingredientes.push({
            id_ingrediente_siesa: ingredienteId
        });
    });

    if (hayErrores) {
        alert('Seleccione un ingrediente en cada fila');
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                ingredientes: ingredientes
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ ${ingredientes.length} ingrediente(s) agregado(s) exitosamente`);
            cerrarModalIngredientes();
            cargarIngredientesPreparacion(preparacionId);
        } else {
            alert('Error: ' + (data.error || 'No se pudieron guardar los ingredientes'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar ingredientes');
    }
}
function cerrarModalIngredientes() {
    // Destruir todas las instancias de Select2 antes de limpiar
    $('.select-ingrediente').each(function() {
        if ($(this).hasClass('select2-hidden-accessible')) {
            $(this).select2('destroy');
        }
    });

    document.getElementById('modalAgregarIngredientes').style.display = 'none';
    document.getElementById('tbodyIngredientes').innerHTML = '';
}
async function eliminarIngrediente(preparacionId, ingredienteId) {
    if (!confirm('¿Está seguro de eliminar este ingrediente?')) {
        return;
    }
    try {
        const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/${ingredienteId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        if (data.success) {
            alert('✓ Ingrediente eliminado exitosamente');
            cargarIngredientesPreparacion(preparacionId);
        } else {
            alert('Error: ' + (data.error || 'No se pudo eliminar'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el ingrediente');
    }
}
function resetearFiltros() {
    document.getElementById('filtroPrograma').innerHTML = '<option value="">Primero seleccione un municipio...</option>';
    document.getElementById('filtroPrograma').disabled = true;
    document.getElementById('btnAplicarFiltros').disabled = true;
    document.getElementById('infoProgramaContainer').style.display = 'none';
    document.getElementById('modalidadesContainer').innerHTML = '';
    document.getElementById('mensajeInicial').style.display = 'block';
}
// Cerrar modales
// Manejador de cierre de modales con delegación de eventos
document.addEventListener('click', function(event) {
    // Cerrar modal al hacer click en la X
    if (event.target.classList.contains('close') && event.target.closest('.modal')) {
        event.target.closest('.modal').style.display = 'none';
    }

    // Cerrar modal al hacer click fuera del contenido
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});
function abrirModalMenuEspecial(modalidadId) {
    // Guardar modalidad actual en variable global o en el modal
    document.getElementById('modalidadIdEspecial').value = modalidadId;
    document.getElementById('nombreMenuEspecial').value = '';
    document.getElementById('modalMenuEspecial').style.display = 'block';
}
async function crearMenuEspecial() {
    const modalidadId = document.getElementById('modalidadIdEspecial').value;
    const nombreMenu = document.getElementById('nombreMenuEspecial').value.trim();
    if (!nombreMenu) {
        alert('Por favor ingrese un nombre para el menú especial');
        return;
    }
    try {
        const response = await fetch('/nutricion/api/crear-menu-especial/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                programa_id: programaActual.id,
                modalidad_id: modalidadId,
                nombre_menu: nombreMenu
            })
        });
        const data = await response.json();
        if (data.success) {
            alert(`✓ Menú especial "${nombreMenu}" creado exitosamente`);
            document.getElementById('modalMenuEspecial').style.display = 'none';
            // Recargar modalidades para mostrar el nuevo menú
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudo crear el menú especial'));
        }
    } catch (error) {
        alert('Error al crear menú especial');
    }
}
// getCookie() ahora disponible desde NutricionUtils.getCookie()

// =================== FUNCIONES PARA MENÚS ESPECIALES ===================

function abrirEditarMenuEspecial(menuId, nombreActual) {
    // Guardar ID del menú en un campo oculto
    document.getElementById('menuIdEditar').value = menuId;
    document.getElementById('nombreMenuEditado').value = nombreActual;
    document.getElementById('modalEditarMenuEspecial').style.display = 'block';
}

async function guardarEdicionMenuEspecial() {
    const menuId = document.getElementById('menuIdEditar').value;
    const nuevoNombre = document.getElementById('nombreMenuEditado').value.trim();

    if (!nuevoNombre) {
        alert('Por favor ingrese un nombre para el menú');
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/menus/${menuId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                menu: nuevoNombre
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ Menú actualizado a "${nuevoNombre}" exitosamente`);
            document.getElementById('modalEditarMenuEspecial').style.display = 'none';
            // Recargar modalidades para reflejar el cambio
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudo actualizar el menú'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al actualizar el menú especial');
    }
}

async function eliminarMenuEspecial(menuId, nombreMenu) {
    if (!confirm(`¿Está seguro de eliminar el menú especial "${nombreMenu}"?\n\nEsta acción también eliminará todas las preparaciones asociadas.`)) {
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/menus/${menuId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ Menú especial "${nombreMenu}" eliminado exitosamente`);
            // Recargar modalidades para reflejar el cambio
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudo eliminar el menú'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el menú especial');
    }
}

// =================== ANÁLISIS NUTRICIONAL ===================

let menuActualAnalisis = null;

// Inicializar evento del botón de análisis nutricional
document.addEventListener('DOMContentLoaded', function() {
    const btnAnalisis = document.getElementById('btnAnalisisNutricional');
    if (btnAnalisis) {
        btnAnalisis.addEventListener('click', function() {
            if (menuActualAnalisis) {
                abrirModalAnalisisNutricional(menuActualAnalisis);
            }
        });
    }
});

function abrirModalAnalisisNutricional(menuId) {
    // Abrir el modal independiente
    const modal = document.getElementById('modalAnalisisNutricional');
    modal.style.display = 'block';

    // Actualizar el título con el nombre del menú
    const menuNumero = document.getElementById('menuNumeroModal').textContent;
    document.getElementById('menuNombreAnalisis').textContent = menuNumero;

    // Cargar el análisis
    cargarAnalisisNutricional(menuId);
}

async function cargarAnalisisNutricional(menuId) {
    try {
        const contenidoAnalisis = document.getElementById('contenidoAnalisis');

        // Mostrar mensaje de carga
        contenidoAnalisis.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin fa-3x"></i><p>Calculando análisis nutricional...</p></div>';

        // Llamar a la API
        const response = await fetch(`/nutricion/api/menus/${menuId}/analisis-nutricional/`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Error al cargar análisis');
        }

        // Renderizar el análisis
        renderizarAnalisisNutricional(data);

    } catch (error) {
        console.error('Error al cargar análisis nutricional:', error);
        document.getElementById('contenidoAnalisis').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> Error al cargar el análisis nutricional: ${error.message}
            </div>
        `;
    }
}

function cerrarModalAnalisisNutricional() {
    document.getElementById('modalAnalisisNutricional').style.display = 'none';
}

function renderizarAnalisisNutricional(data) {
    // Almacenar datos del menú para guardado automático
    window.menuActual = data.menu;
    window.datosNutricionales = data;
    
    const contenidoAnalisis = document.getElementById('contenidoAnalisis');

    if (!data.success) {
        contenidoAnalisis.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Error: ${data.error}
            </div>
        `;
        return;
    }

    const { menu, analisis_por_nivel } = data;
    
    // Almacenar requerimientos globalmente para recálculos
    window.requerimientosNiveles = {};
    analisis_por_nivel.forEach((nivel, index) => {
        window.requerimientosNiveles[index] = nivel.requerimientos;
    });

    contenidoAnalisis.innerHTML = `
        <!-- Información del Menú -->
        <div class="menu-info-header">
            <h4><i class="fas fa-utensils"></i> ${menu.nombre}</h4>
            <div class="menu-details">
                <span class="badge badge-primary">Programa: ${menu.programa}</span>
                <span class="badge badge-secondary">Modalidad: ${menu.modalidad}</span>
            </div>
        </div>
        
        <!-- Análisis por Niveles Escolares -->
        <div class="analisis-niveles-container">
            <h5><i class="fas fa-graduation-cap"></i> Análisis por Nivel Escolar</h5>
            <div class="niveles-accordion" id="nivelesAccordion">
                ${analisis_por_nivel.map((nivel, index) => crearAccordionNivelEscolar(nivel, index)).join('')}
            </div>
        </div>
    `;
    
    // Inicializar eventos para inputs dinámicos
    inicializarEventosInputs();
}

function toggleIngredientes(prepId) {
    const elemento = document.getElementById(prepId);
    const boton = elemento.previousElementSibling;

    if (elemento.style.display === 'none') {
        elemento.style.display = 'block';
        boton.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar Ingredientes';
    } else {
        elemento.style.display = 'none';
        const numIngredientes = elemento.querySelectorAll('.ingrediente-detalle').length;
        boton.innerHTML = `<i class="fas fa-chevron-down"></i> Ver Ingredientes (${numIngredientes})`;
    }
}

// =================== FUNCIONES PARA ANÁLISIS DINÁMICO ===================

function crearAccordionNivelEscolar(nivel, index) {
    const cardId = `collapse-${index}`;
    
    return `
        <div class="card nivel-card">
            <div class="card-header" id="heading-${index}">
                <h6 class="mb-0">
                    <button class="btn btn-link nivel-header-btn ${index === 0 ? '' : 'collapsed'}" type="button" 
                            data-target="#${cardId}" 
                            aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="${cardId}">
                        <i class="fas fa-graduation-cap"></i>
                        ${nivel.nivel_escolar.nombre}
                        <div class="nivel-summary">
                            <span class="badge badge-primary">${nivel.totales.calorias_kcal.toFixed(0)} Kcal</span>
                            <span class="badge badge-success">${nivel.totales.peso_neto_total.toFixed(0)}g neto</span>
                            <span class="badge badge-warning">${nivel.totales.peso_bruto_total.toFixed(0)}g bruto</span>
                        </div>
                        <i class="fas fa-chevron-down toggle-icon" style="transform: ${index === 0 ? 'rotate(180deg)' : 'rotate(0deg)'}"></i>
                    </button>
                </h6>
            </div>
            
            <div id="${cardId}" class="collapse ${index === 0 ? 'show' : ''}" 
                 aria-labelledby="heading-${index}" data-parent="#nivelesAccordion">
                <div class="card-body">
                    <!-- Totales del Nivel -->
                    <div class="nivel-totales mb-3">
                        <h6><i class="fas fa-calculator"></i> Totales del Nivel</h6>
                        <div class="totales-grid-mini">
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.calorias_kcal.estado}">
                                <span>Calorías:</span>
                                <span class="value" id="nivel-${index}-calorias">${nivel.totales.calorias_kcal.toFixed(1)} Kcal</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.proteina_g.estado}">
                                <span>Proteína:</span>
                                <span class="value" id="nivel-${index}-proteina">${nivel.totales.proteina_g.toFixed(1)} g</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.grasa_g.estado}">
                                <span>Grasa:</span>
                                <span class="value" id="nivel-${index}-grasa">${nivel.totales.grasa_g.toFixed(1)} g</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.cho_g.estado}">
                                <span>CHO:</span>
                                <span class="value" id="nivel-${index}-cho">${nivel.totales.cho_g.toFixed(1)} g</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.calcio_mg.estado}">
                                <span>Calcio:</span>
                                <span class="value" id="nivel-${index}-calcio">${nivel.totales.calcio_mg.toFixed(1)} mg</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.hierro_mg.estado}">
                                <span>Hierro:</span>
                                <span class="value" id="nivel-${index}-hierro">${nivel.totales.hierro_mg.toFixed(1)} mg</span>
                            </div>
                            <div class="total-mini" data-estado="${nivel.porcentajes_adecuacion.sodio_mg.estado}">
                                <span>Sodio:</span>
                                <span class="value" id="nivel-${index}-sodio">${nivel.totales.sodio_mg.toFixed(1)} mg</span>
                            </div>
                        </div>
                        
                        <!-- Requerimientos del Nivel -->
                        <h6 class="mt-3"><i class="fas fa-target"></i> Requerimientos</h6>
                        <div class="requerimientos-grid-mini">
                            <div class="requerimiento-mini">
                                <span>Calorías:</span>
                                <span class="value">${nivel.requerimientos.calorias_kcal.toFixed(1)} Kcal</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>Proteína:</span>
                                <span class="value">${nivel.requerimientos.proteina_g.toFixed(1)} g</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>Grasa:</span>
                                <span class="value">${nivel.requerimientos.grasa_g.toFixed(1)} g</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>CHO:</span>
                                <span class="value">${nivel.requerimientos.cho_g.toFixed(1)} g</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>Calcio:</span>
                                <span class="value">${nivel.requerimientos.calcio_mg.toFixed(1)} mg</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>Hierro:</span>
                                <span class="value">${nivel.requerimientos.hierro_mg.toFixed(1)} mg</span>
                            </div>
                            <div class="requerimiento-mini">
                                <span>Sodio:</span>
                                <span class="value">${nivel.requerimientos.sodio_mg.toFixed(1)} mg</span>
                            </div>
                        </div>
                        
                        <!-- Porcentajes de Adecuación -->
                        <h6 class="mt-3"><i class="fas fa-percentage"></i> % de Adecuación (Editable)</h6>
                        <div class="adecuacion-grid-mini">
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.calorias_kcal.estado}">
                                <span>Calorías:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-calorias-pct"
                                       value="${nivel.porcentajes_adecuacion.calorias_kcal.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="calorias_kcal"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.proteina_g.estado}">
                                <span>Proteína:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-proteina-pct"
                                       value="${nivel.porcentajes_adecuacion.proteina_g.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="proteina_g"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.grasa_g.estado}">
                                <span>Grasa:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-grasa-pct"
                                       value="${nivel.porcentajes_adecuacion.grasa_g.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="grasa_g"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.cho_g.estado}">
                                <span>CHO:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-cho-pct"
                                       value="${nivel.porcentajes_adecuacion.cho_g.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="cho_g"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.calcio_mg.estado}">
                                <span>Calcio:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-calcio-pct"
                                       value="${nivel.porcentajes_adecuacion.calcio_mg.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="calcio_mg"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.hierro_mg.estado}">
                                <span>Hierro:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-hierro-pct"
                                       value="${nivel.porcentajes_adecuacion.hierro_mg.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="hierro_mg"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                            <div class="adecuacion-mini" data-estado="${nivel.porcentajes_adecuacion.sodio_mg.estado}">
                                <span>Sodio:</span>
                                <input type="number" 
                                       class="form-control form-control-sm porcentaje-input" 
                                       id="nivel-${index}-sodio-pct"
                                       value="${nivel.porcentajes_adecuacion.sodio_mg.porcentaje}" 
                                       min="0" 
                                       max="100" 
                                       step="0.1"
                                       data-nutriente="sodio_mg"
                                       data-nivel="${index}">
                                <span class="porcentaje-symbol">%</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Preparaciones e Ingredientes -->
                    <div class="preparaciones-container">
                        <h6><i class="fas fa-list-ul"></i> Preparaciones e Ingredientes</h6>
                        ${nivel.preparaciones.map((prep, prepIndex) => crearPreparacion(prep, index, prepIndex)).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function crearPreparacion(preparacion, nivelIndex, prepIndex) {
    return `
        <div class="preparacion-item">
            <h6 class="preparacion-titulo">
                <i class="fas fa-utensils"></i> ${preparacion.nombre}
            </h6>
            <div class="ingredientes-table">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Ingrediente</th>
                            <th>Peso Neto (g)</th>
                            <th>Peso Bruto (g)</th>
                            <th>% Comestible</th>
                            <th>Calorías (kcal)</th>
                            <th>Proteína (g)</th>
                            <th>Grasa (g)</th>
                            <th>CHO (g)</th>
                            <th>Calcio (mg)</th>
                            <th>Hierro (mg)</th>
                            <th>Sodio (mg)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${preparacion.ingredientes.map((ing, ingIndex) => {
                            // Agregar id_preparacion_real al ingrediente para poder recuperarlo después
                            ing.id_preparacion_real = preparacion.id_preparacion;
                            return crearFilaIngrediente(ing, nivelIndex, prepIndex, ingIndex);
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function crearFilaIngrediente(ingrediente, nivelIndex, prepIndex, ingIndex) {
    const inputId = `peso-${nivelIndex}-${prepIndex}-${ingIndex}`;
    const valores = ingrediente.valores_por_100g;

    return `
        <tr class="ingrediente-row"
            data-nivel="${nivelIndex}"
            data-prep="${prepIndex}"
            data-ing="${ingIndex}"
            data-prep-id="${ingrediente.id_preparacion_real || prepIndex}"
            data-ing-id="${ingrediente.id_ingrediente || ingrediente.id_ingrediente_siesa || ingIndex}">
            <td class="ingrediente-nombre">${ingrediente.nombre}</td>
            <td>
                <input type="number"
                       class="form-control form-control-sm peso-input"
                       id="${inputId}"
                       value="${ingrediente.peso_neto_base.toFixed(0)}"
                       min="0"
                       step="1"
                       data-base="${ingrediente.peso_neto_base}"
                       data-parte-comestible="${ingrediente.parte_comestible}"
                       data-calorias="${valores.calorias_kcal}"
                       data-proteina="${valores.proteina_g}"
                       data-grasa="${valores.grasa_g}"
                       data-cho="${valores.cho_g}"
                       data-calcio="${valores.calcio_mg}"
                       data-hierro="${valores.hierro_mg}"
                       data-sodio="${valores.sodio_mg}"
                       data-prep-id="${ingrediente.id_preparacion_real || prepIndex}"
                       data-ing-id="${ingrediente.id_ingrediente || ingrediente.id_ingrediente_siesa || ingIndex}">
            </td>
            <td class="peso-bruto-calc" id="bruto-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${ingrediente.peso_bruto_base.toFixed(0)}
            </td>
            <td class="parte-comestible">${ingrediente.parte_comestible}%</td>
            <td class="nutriente-cal" id="cal-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.calorias_kcal.toFixed(1)}
            </td>
            <td class="nutriente-prot" id="prot-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.proteina_g.toFixed(1)}
            </td>
            <td class="nutriente-grasa" id="grasa-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.grasa_g.toFixed(1)}
            </td>
            <td class="nutriente-cho" id="cho-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.cho_g.toFixed(1)}
            </td>
            <td class="nutriente-calcio" id="calcio-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.calcio_mg.toFixed(1)}
            </td>
            <td class="nutriente-hierro" id="hierro-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.hierro_mg.toFixed(1)}
            </td>
            <td class="nutriente-sodio" id="sodio-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${valores.sodio_mg.toFixed(1)}
            </td>
        </tr>
    `;
}

function inicializarEventosInputs() {
    // Variable para evitar loops infinitos durante sincronización
    let actualizandoPorPeso = false;
    let actualizandoPorPorcentaje = false;
    
    /**
     * Evento para cambios en inputs de peso neto.
     * FLUJO: Peso Neto → Peso Bruto → Valores Nutricionales → Totales → % Adecuación
     *
     * FÓRMULAS:
     * - Peso Bruto = (Peso Neto × 100) / Parte Comestible
     * - Nutriente = (Nutriente por 100g × Peso Neto) / 100
     * - % Adecuación = (Total Nutriente / Requerimiento) × 100
     */
    $(document).on('input change', '.peso-input', function() {
        if (actualizandoPorPorcentaje) return; // Evitar loop infinito

        actualizandoPorPeso = true;

        const input = $(this);
        const nivelIndex = input.closest('.ingrediente-row').data('nivel');
        const prepIndex = input.closest('.ingrediente-row').data('prep');
        const ingIndex = input.closest('.ingrediente-row').data('ing');

        // Obtener valores del input y data attributes
        const pesoNeto = Math.max(0, parseFloat(input.val()) || 0); // Validar >= 0
        const parteComestible = parseFloat(input.data('parte-comestible')) || 100;
        const caloriasPor100g = parseFloat(input.data('calorias')) || 0;
        const proteinaPor100g = parseFloat(input.data('proteina')) || 0;
        const grasaPor100g = parseFloat(input.data('grasa')) || 0;
        const choPor100g = parseFloat(input.data('cho')) || 0;
        const calcioPor100g = parseFloat(input.data('calcio')) || 0;
        const hierroPor100g = parseFloat(input.data('hierro')) || 0;
        const sodioPor100g = parseFloat(input.data('sodio')) || 0;

        // CÁLCULO 1: Peso Bruto desde Peso Neto
        // Fórmula: Peso Bruto = (Peso Neto × 100) / % Parte Comestible
        // Ejemplo: 80g neto con 85% comestible = (80 × 100) / 85 = 94.1g bruto
        const pesoBruto = parteComestible > 0 ? (pesoNeto * 100) / parteComestible : pesoNeto;

        // CÁLCULO 2: Valores nutricionales
        // Fórmula: Nutriente = (Nutriente por 100g × Peso Neto) / 100
        // Ejemplo: 50 kcal/100g en 80g neto = (50 × 80) / 100 = 40 kcal
        const factor = pesoNeto / 100;
        const calorias = caloriasPor100g * factor;
        const proteina = proteinaPor100g * factor;
        const grasa = grasaPor100g * factor;
        const cho = choPor100g * factor;
        const calcio = calcioPor100g * factor;
        const hierro = hierroPor100g * factor;
        const sodio = sodioPor100g * factor;

        // Actualizar peso bruto en la interfaz
        $(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text(pesoBruto.toFixed(0));

        // Actualizar nutrientes en la interfaz
        $(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text(calorias.toFixed(1));
        $(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text(proteina.toFixed(1));
        $(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text(grasa.toFixed(1));
        $(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text(cho.toFixed(1));
        $(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text(calcio.toFixed(1));
        $(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text(hierro.toFixed(1));
        $(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text(sodio.toFixed(1));

        // CÁLCULO 3: Recalcular totales del nivel y porcentajes de adecuación
        recalcularTotalesNivel(nivelIndex);

        actualizandoPorPeso = false;
    });
    
    // Eventos para inputs de porcentaje de adecuación
    let timeoutPorcentaje = null;

    $(document).on('change', '.porcentaje-input', function() {
        if (actualizandoPorPeso) return; // Evitar loop

        const input = $(this);
        const nivelIndex = input.data('nivel');
        const nutriente = input.data('nutriente');
        const porcentajeDeseado = parseFloat(input.val()) || 0;

        // Validar rango 0-100
        if (porcentajeDeseado < 0) {
            input.val(0);
            return;
        }
        if (porcentajeDeseado > 100) {
            input.val(100);
            return;
        }

        // Debounce para evitar múltiples ejecuciones
        clearTimeout(timeoutPorcentaje);
        timeoutPorcentaje = setTimeout(() => {
            actualizandoPorPorcentaje = true;

            console.log('Editando porcentaje:', { nivelIndex, nutriente, porcentajeDeseado });

            // Calcular desde porcentaje hacia pesos
            calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado);

            actualizandoPorPorcentaje = false;
        }, 300); // Esperar 300ms después del último cambio
    });
    
    // Eventos para accordion de niveles escolares
    $(document).on('click', '.nivel-header-btn', function(e) {
        e.preventDefault();
        const button = $(this);
        const targetId = button.data('target');
        const target = $(targetId);
        const icon = button.find('.toggle-icon');

        if (target.hasClass('show')) {
            // Cerrar este accordion
            target.removeClass('show');
            button.attr('aria-expanded', 'false').addClass('collapsed');
            icon.css('transform', 'rotate(0deg)');
        } else {
            // Cerrar todos los otros accordions
            $('.nivel-card .collapse.show').each(function() {
                const otherCollapse = $(this);
                const otherButton = $(`[data-target="#${otherCollapse.attr('id')}"]`);
                const otherIcon = otherButton.find('.toggle-icon');

                otherCollapse.removeClass('show');
                otherButton.attr('aria-expanded', 'false').addClass('collapsed');
                otherIcon.css('transform', 'rotate(0deg)');
            });

            // Abrir este accordion
            target.addClass('show');
            button.attr('aria-expanded', 'true').removeClass('collapsed');
            icon.css('transform', 'rotate(180deg)');
        }
    });
}

function recalcularTotalesNivel(nivelIndex, skipAutoSave = false) {
    let totalCalorias = 0;
    let totalProteina = 0;
    let totalGrasa = 0;
    let totalCho = 0;
    let totalCalcio = 0;
    let totalHierro = 0;
    let totalSodio = 0;
    let totalPesoNeto = 0;
    let totalPesoBruto = 0;

    // Sumar todos los ingredientes del nivel
    $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
        const fila = $(this);
        const prepIndex = fila.data('prep');
        const ingIndex = fila.data('ing');

        const calorias = parseFloat($(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const proteina = parseFloat($(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const grasa = parseFloat($(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const cho = parseFloat($(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const calcio = parseFloat($(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const hierro = parseFloat($(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const sodio = parseFloat($(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
        const pesoNeto = parseFloat(fila.find('.peso-input').val()) || 0;
        const pesoBruto = parseFloat($(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;

        totalCalorias += calorias;
        totalProteina += proteina;
        totalGrasa += grasa;
        totalCho += cho;
        totalCalcio += calcio;
        totalHierro += hierro;
        totalSodio += sodio;
        totalPesoNeto += pesoNeto;
        totalPesoBruto += pesoBruto;
    });

    // Actualizar totales en la interfaz (dentro del card-body)
    $(`#nivel-${nivelIndex}-calorias`).text(`${totalCalorias.toFixed(1)} Kcal`);
    $(`#nivel-${nivelIndex}-proteina`).text(`${totalProteina.toFixed(1)} g`);
    $(`#nivel-${nivelIndex}-grasa`).text(`${totalGrasa.toFixed(1)} g`);
    $(`#nivel-${nivelIndex}-cho`).text(`${totalCho.toFixed(1)} g`);
    $(`#nivel-${nivelIndex}-calcio`).text(`${totalCalcio.toFixed(1)} mg`);
    $(`#nivel-${nivelIndex}-hierro`).text(`${totalHierro.toFixed(1)} mg`);
    $(`#nivel-${nivelIndex}-sodio`).text(`${totalSodio.toFixed(1)} mg`);

    // Actualizar badges en el header del acordeón
    const headerButton = $(`#heading-${nivelIndex}`).find('.nivel-header-btn');
    const badges = headerButton.find('.nivel-summary');
    badges.html(`
        <span class="badge badge-primary">${totalCalorias.toFixed(0)} Kcal</span>
        <span class="badge badge-success">${totalPesoNeto.toFixed(0)}g neto</span>
        <span class="badge badge-warning">${totalPesoBruto.toFixed(0)}g bruto</span>
    `);

    // Recalcular porcentajes de adecuación
    recalcularPorcentajesAdecuacion(nivelIndex, {
        calorias_kcal: totalCalorias,
        proteina_g: totalProteina,
        grasa_g: totalGrasa,
        cho_g: totalCho,
        calcio_mg: totalCalcio,
        hierro_mg: totalHierro,
        sodio_mg: totalSodio
    });

    // Guardado automático después de los cálculos (solo si no se omite)
    if (!skipAutoSave && window.menuActual && window.menuActual.id) {
        setTimeout(() => {
            guardarAnalisisAutomatico(nivelIndex, window.menuActual.id);
        }, 500); // Pequeño delay para asegurar que todos los cálculos terminen
    }
}

/**
 * Calcula y ajusta los pesos de los ingredientes desde el porcentaje de adecuación deseado.
 * MEJORA: Distribuye proporcionalmente el ajuste entre TODOS los ingredientes que aportan el nutriente,
 * manteniendo las proporciones originales de la receta.
 *
 * @param {number} nivelIndex - Índice del nivel escolar
 * @param {string} nutriente - Nutriente a ajustar (ej: 'calorias_kcal', 'proteina_g')
 * @param {number} porcentajeDeseado - Porcentaje de adecuación deseado (0-100)
 */
function calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado) {
    // Obtener el requerimiento nutricional para este nivel y nutriente
    if (!window.requerimientosNiveles || !window.requerimientosNiveles[nivelIndex]) {
        console.warn('No hay datos nutricionales disponibles para nivel:', nivelIndex);
        return;
    }

    const requerimientos = window.requerimientosNiveles[nivelIndex];

    // Mapeo de nombres de nutrientes a claves de requerimientos
    const nutrienteMap = {
        'calorias_kcal': 'calorias_kcal',
        'calorias': 'calorias_kcal',
        'proteina_g': 'proteina_g',
        'proteina': 'proteina_g',
        'grasa_g': 'grasa_g',
        'grasa': 'grasa_g',
        'cho_g': 'cho_g',
        'cho': 'cho_g',
        'calcio_mg': 'calcio_mg',
        'calcio': 'calcio_mg',
        'hierro_mg': 'hierro_mg',
        'hierro': 'hierro_mg',
        'sodio_mg': 'sodio_mg',
        'sodio': 'sodio_mg'
    };

    const nutrienteKey = nutrienteMap[nutriente];
    const requerimientoNecesario = requerimientos[nutrienteKey] || 0;

    if (requerimientoNecesario === 0) {
        console.warn('Requerimiento no encontrado para:', nutriente);
        return;
    }

    // Calcular el valor objetivo del nutriente (limitado entre 0-100%)
    const porcentajeValido = Math.max(0, Math.min(100, porcentajeDeseado));
    const valorObjetivo = (porcentajeValido * requerimientoNecesario) / 100;

    console.log(`[${nutriente}] Objetivo: ${valorObjetivo.toFixed(2)} (${porcentajeValido}% de ${requerimientoNecesario})`);

    // Recolectar información de todos los ingredientes con sus aportes actuales
    const ingredientesData = [];
    let valorActualTotal = 0;

    $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
        const row = $(this);
        const pesoInput = row.find('.peso-input');
        const prepIndex = row.data('prep');
        const ingIndex = row.data('ing');
        const pesoActual = parseFloat(pesoInput.val()) || 0;

        // Obtener nutriente por 100g del data attribute
        let nutrientePor100g = 0;
        switch (nutrienteKey) {
            case 'calorias_kcal':
                nutrientePor100g = parseFloat(pesoInput.data('calorias')) || 0;
                break;
            case 'proteina_g':
                nutrientePor100g = parseFloat(pesoInput.data('proteina')) || 0;
                break;
            case 'grasa_g':
                nutrientePor100g = parseFloat(pesoInput.data('grasa')) || 0;
                break;
            case 'cho_g':
                nutrientePor100g = parseFloat(pesoInput.data('cho')) || 0;
                break;
            case 'calcio_mg':
                nutrientePor100g = parseFloat(pesoInput.data('calcio')) || 0;
                break;
            case 'hierro_mg':
                nutrientePor100g = parseFloat(pesoInput.data('hierro')) || 0;
                break;
            case 'sodio_mg':
                nutrientePor100g = parseFloat(pesoInput.data('sodio')) || 0;
                break;
        }

        const valorActual = (nutrientePor100g * pesoActual) / 100;
        valorActualTotal += valorActual;

        // Solo guardar ingredientes que aportan este nutriente
        if (nutrientePor100g > 0.1) {
            ingredientesData.push({
                pesoInput: pesoInput,
                nutrientePor100g: nutrientePor100g,
                pesoActual: pesoActual,
                valorActual: valorActual,
                prepIndex: prepIndex,
                ingIndex: ingIndex,
                row: row
            });
        }
    });

    if (ingredientesData.length === 0) {
        console.warn('No hay ingredientes que aporten el nutriente:', nutriente);
        return;
    }

    // Calcular cuánto necesitamos ajustar
    const diferencia = valorObjetivo - valorActualTotal;

    if (Math.abs(diferencia) < 0.01) {
        console.log('El valor actual ya está muy cerca del objetivo');
        return;
    }

    console.log(`Diferencia a ajustar: ${diferencia.toFixed(2)}`);

    // ESTRATEGIA DE AJUSTE PROPORCIONAL:
    // Calcular el factor de escala proporcional para mantener las proporciones de la receta
    const factorEscala = valorActualTotal > 0 ? (valorObjetivo / valorActualTotal) : 1;

    // Aplicar el factor de escala a todos los ingredientes que aportan el nutriente
    ingredientesData.forEach(ing => {
        const nuevoPeso = ing.pesoActual * factorEscala;

        // Aplicar el nuevo peso con validación (mínimo 0g)
        const pesoFinal = Math.max(0, nuevoPeso);

        ing.pesoInput.val(pesoFinal.toFixed(1));

        console.log(`  - Ingrediente [${ing.prepIndex}-${ing.ingIndex}]: ${ing.pesoActual.toFixed(1)}g → ${pesoFinal.toFixed(1)}g`);
    });

    // Recalcular manualmente todos los valores nutricionales sin disparar eventos
    ingredientesData.forEach(ing => {
        const pesoNeto = parseFloat(ing.pesoInput.val()) || 0;
        const parteComestible = parseFloat(ing.pesoInput.data('parte-comestible')) || 100;
        const factor = pesoNeto / 100;

        // Calcular peso bruto
        const pesoBruto = parteComestible > 0 ? (pesoNeto * 100) / parteComestible : pesoNeto;

        // Calcular nutrientes
        const calorias = (parseFloat(ing.pesoInput.data('calorias')) || 0) * factor;
        const proteina = (parseFloat(ing.pesoInput.data('proteina')) || 0) * factor;
        const grasa = (parseFloat(ing.pesoInput.data('grasa')) || 0) * factor;
        const cho = (parseFloat(ing.pesoInput.data('cho')) || 0) * factor;
        const calcio = (parseFloat(ing.pesoInput.data('calcio')) || 0) * factor;
        const hierro = (parseFloat(ing.pesoInput.data('hierro')) || 0) * factor;
        const sodio = (parseFloat(ing.pesoInput.data('sodio')) || 0) * factor;

        // Actualizar UI directamente
        $(`#bruto-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(pesoBruto.toFixed(0));
        $(`#cal-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(calorias.toFixed(1));
        $(`#prot-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(proteina.toFixed(1));
        $(`#grasa-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(grasa.toFixed(1));
        $(`#cho-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(cho.toFixed(1));
        $(`#calcio-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(calcio.toFixed(1));
        $(`#hierro-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(hierro.toFixed(1));
        $(`#sodio-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(sodio.toFixed(1));
    });

    // Recalcular totales una sola vez al final (sin guardado automático)
    recalcularTotalesNivel(nivelIndex, true); // true = skip auto-save

    console.log(`✓ Ajuste proporcional completado para ${nutriente} (factor: ${factorEscala.toFixed(3)})`);
}

function recalcularPorcentajesAdecuacion(nivelIndex, totales) {
    console.log('Recalculando porcentajes para nivel:', nivelIndex, 'totales:', totales);
    
    // Obtener requerimientos desde los datos almacenados globalmente
    const requerimientos = window.requerimientosNiveles && window.requerimientosNiveles[nivelIndex];
    
    if (!requerimientos) {
        console.warn(`No se encontraron requerimientos para nivel ${nivelIndex}`);
        console.log('window.requerimientosNiveles:', window.requerimientosNiveles);
        return;
    }
    
    const nutrientes = [
        { key: 'calorias_kcal', id: 'calorias' },
        { key: 'proteina_g', id: 'proteina' },
        { key: 'grasa_g', id: 'grasa' },
        { key: 'cho_g', id: 'cho' },
        { key: 'calcio_mg', id: 'calcio' },
        { key: 'hierro_mg', id: 'hierro' },
        { key: 'sodio_mg', id: 'sodio' }
    ];
    
    nutrientes.forEach(nutriente => {
        const total = totales[nutriente.key] || 0;
        const requerido = requerimientos[nutriente.key] || 1;
        
        // Calcular porcentaje limitado entre 0-100%
        let porcentaje = (total / requerido) * 100;
        porcentaje = Math.min(Math.max(porcentaje, 0), 100); // Limitar entre 0-100
        
        const estado = getEstadoAdecuacion(porcentaje, nutriente.key);
        
        // Actualizar input de porcentaje editable
        const inputPorcentaje = $(`#nivel-${nivelIndex}-${nutriente.id}-pct`);
        if (inputPorcentaje.length) {
            inputPorcentaje.val(porcentaje.toFixed(1));
            inputPorcentaje.closest('.adecuacion-mini').attr('data-estado', estado);
        }
        
        // Actualizar estado de la tarjeta de total
        const elementoTotal = $(`#nivel-${nivelIndex}-${nutriente.id}`);
        if (elementoTotal.length) {
            elementoTotal.closest('.total-mini').attr('data-estado', estado);
        }
    });
}

/**
 * Determina el estado de adecuación nutricional según el porcentaje alcanzado.
 *
 * RANGOS DE EVALUACIÓN (consistentes con el backend Python):
 * - 0-35%: ÓPTIMO (verde) - Aporte bajo pero seguro
 * - 35.1-70%: ACEPTABLE (amarillo) - Aporte moderado
 * - >70%: ALTO (rojo) - Aporte elevado, cerca del límite máximo
 *
 * NOTA: Los rangos son uniformes para todos los nutrientes (incluido sodio).
 * El 100% representa el máximo permitido según ICBF 2018.
 *
 * @param {number} porcentaje - Porcentaje de adecuación (0-100)
 * @param {string} nutriente - Nombre del nutriente (opcional, para futuras extensiones)
 * @returns {string} Estado: 'optimo', 'aceptable', o 'alto'
 */
function getEstadoAdecuacion(porcentaje, nutriente) {
    // Validar y limitar porcentaje entre 0-100
    porcentaje = Math.max(0, Math.min(100, porcentaje));

    // Rangos uniformes para todos los nutrientes
    if (porcentaje <= 35) {
        return 'optimo';      // 0-35%: Verde
    } else if (porcentaje <= 70) {
        return 'aceptable';   // 35.1-70%: Amarillo
    } else {
        return 'alto';        // >70%: Rojo
    }
}

// =================== GUARDADO AUTOMÁTICO ===================

/**
 * Guarda automáticamente el análisis nutricional editado
 * Se ejecuta después de cada cambio en pesos o porcentajes
 */
async function guardarAnalisisAutomatico(nivelIndex, menuId) {
    try {
        // Recopilar totales actuales del nivel
        const totales = {
            calorias: parseFloat($(`#nivel-${nivelIndex}-calorias`).text().replace(' Kcal', '')) || 0,
            proteina: parseFloat($(`#nivel-${nivelIndex}-proteina`).text().replace(' g', '')) || 0,
            grasa: parseFloat($(`#nivel-${nivelIndex}-grasa`).text().replace(' g', '')) || 0,
            cho: parseFloat($(`#nivel-${nivelIndex}-cho`).text().replace(' g', '')) || 0,
            calcio: parseFloat($(`#nivel-${nivelIndex}-calcio`).text().replace(' mg', '')) || 0,
            hierro: parseFloat($(`#nivel-${nivelIndex}-hierro`).text().replace(' mg', '')) || 0,
            sodio: parseFloat($(`#nivel-${nivelIndex}-sodio`).text().replace(' mg', '')) || 0,
            peso_neto: 0,  // Se calculará sumando ingredientes
            peso_bruto: 0  // Se calculará sumando ingredientes
        };

        // Recopilar porcentajes de adecuación
        const porcentajes = {
            calorias: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calorias_kcal"]`).val()) || 0,
            proteina: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="proteina_g"]`).val()) || 0,
            grasa: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="grasa_g"]`).val()) || 0,
            cho: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="cho_g"]`).val()) || 0,
            calcio: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calcio_mg"]`).val()) || 0,
            hierro: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="hierro_mg"]`).val()) || 0,
            sodio: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="sodio_mg"]`).val()) || 0
        };

        // Recopilar datos de ingredientes configurados
        const ingredientes = [];
        $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
            const row = $(this);
            const prepIndex = row.data('prep');
            const ingIndex = row.data('ing');
            const pesoInput = row.find('.peso-input');

            // Obtener IDs reales desde data attributes
            const prepIdReal = row.data('prep-id') || pesoInput.data('prep-id');
            const ingIdReal = row.data('ing-id') || pesoInput.data('ing-id');

            console.log(`[DEBUG] Guardando ingrediente - Índices: prep=${prepIndex}, ing=${ingIndex}, IDs reales: prepId=${prepIdReal}, ingId=${ingIdReal}`);

            const pesoNeto = parseFloat(pesoInput.val()) || 0;
            const pesoBruto = parseFloat($(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;

            const ingrediente = {
                id_preparacion: prepIdReal,
                id_ingrediente_siesa: ingIdReal,
                peso_neto: pesoNeto,
                peso_bruto: pesoBruto,
                calorias: parseFloat($(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                proteina: parseFloat($(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                grasa: parseFloat($(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                cho: parseFloat($(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                calcio: parseFloat($(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                hierro: parseFloat($(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                sodio: parseFloat($(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0
            };

            // Acumular pesos totales
            totales.peso_neto += pesoNeto;
            totales.peso_bruto += pesoBruto;

            ingredientes.push(ingrediente);
        });

        // Obtener ID del nivel escolar desde los datos almacenados
        const idNivelEscolar = datosNutricionales &&
                              datosNutricionales.analisis_por_nivel &&
                              datosNutricionales.analisis_por_nivel[nivelIndex] &&
                              datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar &&
                              datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar.id;

        console.log('[DEBUG] ID Nivel Escolar obtenido:', {
            nivelIndex,
            idNivelEscolar,
            nivel_escolar_completo: datosNutricionales?.analisis_por_nivel?.[nivelIndex]?.nivel_escolar,
            existe_datos: !!datosNutricionales
        });

        if (!idNivelEscolar || idNivelEscolar === '-1' || idNivelEscolar === -1) {
            console.error('ID de nivel escolar inválido:', idNivelEscolar);
            console.error('Datos completos:', datosNutricionales?.analisis_por_nivel?.[nivelIndex]);
            NutricionUtils.mostrarNotificacion('error', 'No se puede guardar: nivel escolar inválido');
            return;
        }

        // Preparar datos para el guardado
        const datosGuardado = {
            id_menu: menuId,
            id_nivel_escolar: idNivelEscolar,
            totales: totales,
            porcentajes: porcentajes,
            ingredientes: ingredientes
        };

        console.log('[GUARDADO AUTOMÁTICO] Datos a enviar:', {
            menuId,
            idNivelEscolar,
            totalIngredientes: ingredientes.length,
            datosCompletos: datosGuardado
        });

        // Enviar datos al servidor
        const response = await fetch('/nutricion/api/guardar-analisis-nutricional/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': NutricionUtils.getCsrfToken()
            },
            body: JSON.stringify(datosGuardado)
        });

        console.log('[GUARDADO AUTOMÁTICO] Response status:', response.status);

        const result = await response.json();
        console.log('[GUARDADO AUTOMÁTICO] Response data:', result);

        if (result.success) {
            console.log('✓ Análisis nutricional guardado automáticamente:', {
                analisisId: result.analisis_id,
                ingredientesGuardados: result.ingredientes_guardados,
                created: result.created
            });

            // Mostrar indicador visual de guardado exitoso
            NutricionUtils.mostrarNotificacion('success', `Guardado: ${result.ingredientes_guardados} ingredientes`);
        } else {
            console.error('✗ Error al guardar análisis nutricional:', result.error);
            NutricionUtils.mostrarNotificacion('error', `Error: ${result.error || 'Desconocido'}`);
        }

    } catch (error) {
        console.error('✗ Error en guardado automático:', error);
        NutricionUtils.mostrarNotificacion('error', `Error: ${error.message || 'Conexión fallida'}`);
    }
}

/**
 * Muestra una notificación visual del estado del guardado
 */
// mostrarNotificacionGuardado() ahora disponible desde NutricionUtils.mostrarNotificacion()

// getCsrfToken() ahora disponible desde NutricionUtils.getCsrfToken()
