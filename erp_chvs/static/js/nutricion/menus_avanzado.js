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
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
    const contenidoAnalisis = document.getElementById('contenidoAnalisis');

    // Mapeo de nombres amigables
    const nombresNutrientes = {
        'calorias': 'Calorías',
        'proteina': 'Proteína',
        'grasa': 'Grasa',
        'cho': 'CHO (Carbohidratos)',
        'calcio': 'Calcio',
        'hierro': 'Hierro',
        'sodio': 'Sodio'
    };

    const unidadesNutrientes = {
        'calorias': 'Kcal',
        'proteina': 'g',
        'grasa': 'g',
        'cho': 'g',
        'calcio': 'mg',
        'hierro': 'mg',
        'sodio': 'mg'
    };

    const keysNutrientes = {
        'calorias': 'calorias_kcal',
        'proteina': 'proteina_g',
        'grasa': 'grasa_g',
        'cho': 'cho_g',
        'calcio': 'calcio_mg',
        'hierro': 'hierro_mg',
        'sodio': 'sodio_mg'
    };

    const estadosTexto = {
        'OPTIMO': '✓ ÓPTIMO',
        'EN_LIMITE': '⚠ CERCA DEL LÍMITE',
        'EXCEDIDO': '❌ EXCEDIDO',
        'SIN_REQUERIMIENTOS': 'ℹ SIN REQUERIMIENTOS CONFIGURADOS'
    };

    let html = '';

    // Información del menú
    html += `<div class="menu-info-card">
        <h3><i class="fas fa-utensils"></i> ${data.menu.nombre}</h3>
        <div class="menu-details">
            <span><strong>Programa:</strong> ${data.menu.programa}</span> |
            <span><strong>Modalidad:</strong> ${data.menu.modalidad}</span>
        </div>
    </div>`;

    // Totales del menú
    html += `<div class="totales-menu-card">
        <h4><i class="fas fa-calculator"></i> TOTALES DEL MENÚ</h4>
        <div class="totales-grid">`;

    for (const [key, nombre] of Object.entries(nombresNutrientes)) {
        const totalKey = keysNutrientes[key];
        const valorActual = data.totales[totalKey];
        const unidad = unidadesNutrientes[key];

        html += `<div class="total-item">
            <span class="total-label">${nombre}:</span>
            <span class="total-value">${valorActual} ${unidad}</span>
        </div>`;
    }

    html += `</div>
    </div>`;

    // Análisis por niveles escolares
    if (data.analisis_por_nivel && data.analisis_por_nivel.length > 0) {
        html += `<div class="analisis-niveles-container">
            <h4><i class="fas fa-graduation-cap"></i> ANÁLISIS POR NIVELES ESCOLARES</h4>
            <div class="niveles-escolares-grid">`;

        data.analisis_por_nivel.forEach(analisis => {
            const esNivelPrograma = analisis.nivel_escolar.es_nivel_programa;
            const claseNivel = esNivelPrograma ? 'nivel-programa-actual' : 'nivel-otro';

            html += `<div class="nivel-escolar-card ${claseNivel}">
                <div class="nivel-header">
                    <h5>
                        ${esNivelPrograma ? '🎯 ' : '📚 '}
                        ${analisis.nivel_escolar.nombre}
                        ${esNivelPrograma ? ' (PROGRAMA ACTUAL)' : ''}
                    </h5>
                    <div class="estado-badge ${analisis.estado_general.toLowerCase()}">
                        ${estadosTexto[analisis.estado_general]}
                    </div>
                </div>`;

            // Nutrientes para este nivel
            html += '<div class="nutrientes-nivel-grid">';
            
            for (const [key, nombre] of Object.entries(nombresNutrientes)) {
                const totalKey = keysNutrientes[key];
                const valorActual = data.totales[totalKey];
                const valorLimite = analisis.requerimientos[totalKey];
                const porcentaje = analisis.porcentajes[key];
                const unidad = unidadesNutrientes[key];

                // Determinar clase de estado
                let estadoClase = 'optimo';
                if (porcentaje > 100) {
                    estadoClase = 'excedido';
                } else if (porcentaje >= 86) {
                    estadoClase = 'en-limite';
                }

                // Limitar el ancho de la barra al 100% visual
                const porcentajeVisual = Math.min(porcentaje, 100);

                html += `
                    <div class="nutriente-row ${estadoClase}">
                        <div class="nutriente-header">
                            <div class="nutriente-nombre">${nombre}</div>
                            <div class="nutriente-valores">
                                <span class="actual">${valorActual}</span> / ${valorLimite} ${unidad}
                            </div>
                        </div>
                        <div class="barra-progreso">
                            <div class="barra-progreso-fill ${estadoClase}" style="width: ${porcentajeVisual}%">
                                ${porcentaje.toFixed(1)}%
                            </div>
                        </div>
                    </div>
                `;
            }

            html += '</div>';

            // Alertas para este nivel
            if (analisis.alertas && analisis.alertas.length > 0) {
                html += '<div class="alertas-nivel">';
                html += '<h6><i class="fas fa-exclamation-triangle"></i> Alertas</h6>';

                analisis.alertas.forEach(alerta => {
                    const claseAlerta = alerta.tipo === 'EXCEDIDO' ? 'excedido' : 'en-limite';
                    const icono = alerta.tipo === 'EXCEDIDO' ? '❌' : '⚠️';
                    const mensaje = alerta.tipo === 'EXCEDIDO'
                        ? `${icono} ${nombresNutrientes[alerta.nutriente]}: ${alerta.valor_actual} / ${alerta.valor_limite} ${unidadesNutrientes[alerta.nutriente]} (${alerta.porcentaje}%) - EXCEDE EL LÍMITE`
                        : `${icono} ${nombresNutrientes[alerta.nutriente]}: ${alerta.porcentaje}% - Cerca del límite`;

                    html += `<div class="alerta-item ${claseAlerta}">${mensaje}</div>`;
                });

                html += '</div>';
            }

            html += '</div>'; // Cerrar nivel-escolar-card
        });

        html += '</div>'; // Cerrar niveles-escolares-grid
        html += '</div>'; // Cerrar analisis-niveles-container

    } else {
        // Sin requerimientos configurados
        html += '<div class="alert alert-warning">';
        html += '<i class="fas fa-exclamation-triangle"></i> <strong>No hay requerimientos nutricionales configurados.</strong><br>';
        html += 'Configure los requerimientos en la tabla de Requerimientos Nutricionales para ver el análisis completo.';
        html += '</div>';
    }

    // Detalle por preparaciones
    if (data.detalle_preparaciones && data.detalle_preparaciones.length > 0) {
        html += '<div class="detalle-preparaciones">';
        html += '<h4><i class="fas fa-utensils"></i> Desglose por Preparación</h4>';

        data.detalle_preparaciones.forEach(prep => {
            html += `<div class="preparacion-detalle-card">`;
            html += `<div class="preparacion-detalle-header">${prep.nombre}</div>`;

            // Totales de la preparación
            html += `<div style="margin-bottom: 10px; font-size: 14px; color: #666;">`;
            html += `<strong>Aporte:</strong> ${prep.totales.calorias_kcal} Kcal | `;
            html += `${prep.totales.proteina_g}g Proteína | `;
            html += `${prep.totales.grasa_g}g Grasa | `;
            html += `${prep.totales.cho_g}g CHO`;
            html += `</div>`;

            // Ingredientes
            if (prep.ingredientes && prep.ingredientes.length > 0) {
                html += `<button class="btn-toggle-detalle" onclick="toggleIngredientes('prep-${prep.id_preparacion}')">`;
                html += `<i class="fas fa-chevron-down"></i> Ver Ingredientes (${prep.ingredientes.length})`;
                html += `</button>`;

                html += `<div id="prep-${prep.id_preparacion}" style="display: none; margin-top: 10px;">`;
                prep.ingredientes.forEach(ing => {
                    if (ing.alimento_encontrado) {
                        html += `<div class="ingrediente-detalle">`;
                        html += `<span>${ing.nombre}</span>`;
                        html += `<span>${ing.calorias} Kcal</span>`;
                        html += `</div>`;
                    } else {
                        html += `<div class="ingrediente-detalle no-encontrado">`;
                        html += `<span>${ing.nombre}</span>`;
                        html += `<span>⚠️ ${ing.mensaje}</span>`;
                        html += `</div>`;
                    }
                });
                html += `</div>`;
            }

            html += `</div>`;
        });

        html += '</div>';
    }

    contenidoAnalisis.innerHTML = html;
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
