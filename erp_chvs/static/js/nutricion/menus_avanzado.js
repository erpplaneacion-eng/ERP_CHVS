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
    const tarjetasMenus = menus.map(menu => `
        <div class="menu-card ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
             onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
            <div class="menu-numero">${menu.menu}</div>
            <div class="menu-actions">
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                    <i class="fas fa-utensils"></i> Preparaciones
                </button>
            </div>
        </div>
    `).join('');
    // Agregar tarjeta para menú especial
    const modalidadId = menus.length > 0 ? menus[0].id_modalidad__id_modalidades : '';
    const tarjetaEspecial = `
        <div class="menu-card menu-card-especial" onclick="abrirModalMenuEspecial('${modalidadId}')">
            <div class="menu-numero-especial">
                <i class="fas fa-plus-circle"></i>
            </div>
            <div class="menu-label-especial">Menú Especial</div>
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
            data.preparaciones.forEach(prep => {
                const accordion = crearAcordeonPreparacion(prep, menuId);
                container.appendChild(accordion);
            });
        } else {
            container.innerHTML = '<div class="no-ingredientes"><i class="fas fa-info-circle"></i> No hay preparaciones asociadas a este menú</div>';
        }
    } catch (error) {
        console.error('Error:', error);
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
                            <i class="fas fa-carrot"></i> ${ing.nombre_ingrediente}
                        </div>
                        <div class="ingrediente-cantidad">
                            <strong>${ing.cantidad || 0}</strong> ${ing.unidad_medida || 'unidades'}
                        </div>
                    </div>
                    <div class="ingrediente-acciones">
                        <button class="btn-icon btn-edit" onclick="editarIngrediente(${preparacionId}, ${ing.id_ingrediente})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-delete" onclick="eliminarIngrediente(${preparacionId}, ${ing.id_ingrediente})" title="Eliminar">
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
        ingredientesSiesa.map(ing => `<option value="${ing.id_ingrediente}">${ing.nombre_ingrediente}</option>`).join('');
    tr.innerHTML = `
        <td>
            <select class="select-ingrediente" id="ingrediente-${filaIndex}" required>
                ${optionsHTML}
            </select>
        </td>
        <td>
            <input type="number" class="input-cantidad" id="cantidad-${filaIndex}"
                   placeholder="0.00" step="0.01" min="0" required>
        </td>
        <td>
            <select class="select-ingrediente" id="unidad-${filaIndex}" required>
                <option value="">Seleccione...</option>
                <option value="kg">Kilogramos (kg)</option>
                <option value="g">Gramos (g)</option>
                <option value="l">Litros (l)</option>
                <option value="ml">Mililitros (ml)</option>
                <option value="unidad">Unidades</option>
                <option value="lb">Libras (lb)</option>
                <option value="oz">Onzas (oz)</option>
            </select>
        </td>
        <td style="text-align: center;">
            <button type="button" class="btn-eliminar-fila" onclick="eliminarFilaIngrediente(${filaIndex})">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
}
function eliminarFilaIngrediente(index) {
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
        const cantidad = document.getElementById(`cantidad-${index}`)?.value;
        const unidad = document.getElementById(`unidad-${index}`)?.value;
        if (!ingredienteId || !cantidad || !unidad) {
            hayErrores = true;
            return;
        }
        ingredientes.push({
            id_ingrediente: parseInt(ingredienteId),
            cantidad: parseFloat(cantidad),
            unidad_medida: unidad
        });
    });
    if (hayErrores) {
        alert('Complete todos los campos de cada fila');
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
        alert('Error al guardar ingredientes');
    }
}
function cerrarModalIngredientes() {
    document.getElementById('modalAgregarIngredientes').style.display = 'none';
    document.getElementById('tbodyIngredientes').innerHTML = '';
}
function editarIngrediente(preparacionId, ingredienteId) {
    alert(`Editar ingrediente ${ingredienteId} de preparación ${preparacionId}`);
    // TODO: Implementar modal de edición
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
document.querySelectorAll('.modal .close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function() {
        this.closest('.modal').style.display = 'none';
    });
});
window.addEventListener('click', function(event) {
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
