// Gestión Avanzada de Menús por Modalidad - Módulo de Nutrición

// =================== VARIABLES GLOBALES ===================
let programaActual = null;
let municipioActual = null;
let modalidadesData = [];
let menusData = {};

// =================== DECLARACIÓN TEMPRANA DE FUNCIONES PARA ONCLICK ===================
// Estas funciones se declaran aquí para que estén disponibles inmediatamente
// Las implementaciones están más abajo en el archivo

// Función para cerrar modal de preparación (implementación provisional)
window.cerrarModalPreparacion = function() {
    const modal = document.getElementById('modalNuevaPreparacion');
    if (modal) modal.style.display = 'none';
};

// Función para cerrar modal de ingredientes (implementación provisional)
window.cerrarModalIngredientes = function() {
    const modal = document.getElementById('modalAgregarIngredientes');
    if (modal) {
        modal.style.display = 'none';
        // Limpiar tabla
        const tbody = document.getElementById('tbodyIngredientes');
        if (tbody) tbody.innerHTML = '';
    }
};

// Función para cerrar modal de análisis (implementación provisional)
window.cerrarModalAnalisisNutricional = function() {
    const modal = document.getElementById('modalAnalisisNutricional');
    if (modal) modal.style.display = 'none';
};

// Función para abrir modal de agregar ingredientes (implementación completa)
window.abrirAgregarIngrediente = async function(preparacionId) {
    console.log('🟢 [COMPLETA] abrirAgregarIngrediente llamada para preparación:', preparacionId);
    
    document.getElementById('preparacionIdIngredientes').value = preparacionId;
    document.getElementById('tbodyIngredientes').innerHTML = '';
    
    if (typeof ingredientesSiesa === 'undefined' || ingredientesSiesa.length === 0) {
        console.log('Cargando ingredientes SIESA...');
        await cargarIngredientesSiesa();
    }
    
    console.log('Agregando primera fila de ingrediente...');
    window.agregarFilaIngrediente();
    
    console.log('✅ Abriendo modal de ingredientes (versión completa)');
    const modal = document.getElementById('modalAgregarIngredientes');
    const modalContent = modal.querySelector('.modal-content');
    
    // MOVER MODAL AL BODY Y FORZAR VISIBILIDAD
    document.body.appendChild(modal);
    
    // FORZAR VISIBILIDAD DEL MODAL
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100vw';
    modal.style.height = '100vh';
    modal.style.zIndex = '9999';
    modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';
    
    // Forzar visibilidad del contenido
    if (modalContent) {
        modalContent.style.display = 'block';
        modalContent.style.visibility = 'visible';
        modalContent.style.opacity = '1';
        modalContent.style.position = 'relative';
        modalContent.style.zIndex = '10000';
        modalContent.style.width = '800px';
        modalContent.style.height = '600px';
        modalContent.style.backgroundColor = 'white';
        modalContent.style.borderRadius = '8px';
        modalContent.style.padding = '20px';
    }
    
    console.log('✅ Modal de ingredientes MOVIDO AL BODY y FORZADO a ser visible');
};

// Función para agregar fila de ingrediente (implementación provisional)
window.agregarFilaIngrediente = function() {
    console.log('Función agregarFilaIngrediente - esperando implementación completa');
};

// Función para guardar ingredientes (implementación provisional)
window.guardarIngredientes = function() {
    console.log('Función guardarIngredientes - esperando implementación completa');
};

// Función para eliminar ingrediente (implementación provisional)
window.eliminarIngrediente = function(preparacionId, ingredienteId) {
    console.log('Eliminando ingrediente:', ingredienteId, 'de preparación:', preparacionId);
};

// Función para eliminar fila de ingrediente (implementación provisional)
window.eliminarFilaIngrediente = function(index) {
    console.log('Eliminando fila:', index);
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando eventos de modales...');
    
    // Asegurar que todos los modales estén ocultos al cargar
    const modalesOcultar = ['modalPreparaciones', 'modalNuevaPreparacion', 'modalAgregarIngredientes', 'modalAnalisisNutricional'];
    modalesOcultar.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            console.log(`✅ ${modalId} oculto`);
        }
    });
    
    // Configurar botones de cerrar (X) para cada modal
    const configurarBotonCerrar = (modalId, funcionCerrar) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            const closeBtn = modal.querySelector('.close');
            if (closeBtn) {
                closeBtn.onclick = funcionCerrar;
                console.log(`✅ Botón cerrar configurado para ${modalId}`);
            }
        }
    };
    
    configurarBotonCerrar('modalPreparaciones', () => {
        document.getElementById('modalPreparaciones').style.display = 'none';
    });
    
    configurarBotonCerrar('modalNuevaPreparacion', window.cerrarModalPreparacion);
    configurarBotonCerrar('modalAgregarIngredientes', window.cerrarModalIngredientes);
    configurarBotonCerrar('modalAnalisisNutricional', window.cerrarModalAnalisisNutricional);
    
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

    const downloadUrl = `/nutricion/exportar-modalidad-excel/${programaActual.id}/${modalidadId}/`;

    header.innerHTML = `
        <div>
            <strong>${modalidad.modalidad}</strong>
            <span class="preparacion-badge">${menusModalidad.length} / 20 menús</span>
        </div>
        <div class="accordion-header-actions">
            <a href="${downloadUrl}" class="btn btn-success btn-sm" onclick="event.stopPropagation();" title="Descargar Reporte Maestro para ${modalidad.modalidad}">
                <i class="fas fa-file-excel"></i> Descargar Modalidad
            </a>
            ${!tieneMenus ? `<button class="btn-generar-auto" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                <i class="fas fa-magic"></i> Generar 20 Menús
            </button>` : ''}
            <i class="fas fa-chevron-down"></i>
        </div>
    `;

    // Agregar event listener al botón de generar menús si existe
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
        const esNumerico = !isNaN(menu.menu) && parseInt(menu.menu) >= 1 && parseInt(menu.menu) <= 20;
        const esEspecial = !esNumerico;
        const menuEscaped = String(menu.menu).replace(/'/g, "\'");
        const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;

        if (esEspecial) {
            return `
                <div class="menu-card menu-card-especial ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                    <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                        <i class="fas fa-file-excel"></i>
                    </a>
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
            return `
                <div class="menu-card ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                    <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                        <i class="fas fa-file-excel"></i>
                    </a>
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
    document.querySelectorAll('.accordion-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.accordion-header').forEach(h => h.classList.remove('active'));
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
let componentesAlimentos = [];
let modalidadActualId = null; // Variable global para la modalidad

function abrirGestionPreparaciones(menuId, menuNumero) {
    menuActualId = menuId;
    menuActualAnalisis = menuId;
    document.getElementById('menuNumeroModal').textContent = menuNumero;
    document.getElementById('modalPreparaciones').style.display = 'block';

    // Encontrar la modalidad del menú actual
    for (const modId in menusData) {
        if (menusData[modId].some(menu => menu.id_menu === menuId)) {
            modalidadActualId = modId;
            break;
        }
    }

    // Configurar botón de agregar preparación
    const btnAgregar = document.getElementById('btnAgregarPreparacion');
    if (btnAgregar) {
        console.log('🔧 Configurando botón Agregar Preparación para menú:', menuId);
        
        // Remover todos los event listeners anteriores
        const newBtn = btnAgregar.cloneNode(true);
        btnAgregar.parentNode.replaceChild(newBtn, btnAgregar);
        
        // Asignar el evento al nuevo botón
        newBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔵 [CLICK] Botón Agregar Preparación - menú:', menuId);
            console.log('🔵 Llamando a abrirModalNuevaPreparacion...');
            abrirModalNuevaPreparacion(menuId);
        };
    } else {
        console.warn('⚠️ Botón btnAgregarPreparacion no encontrado');
    }
    
    cargarPreparacionesMenu(menuId);
}

async function abrirModalNuevaPreparacion(menuId) {
    console.log('🔵 abrirModalNuevaPreparacion llamada para menú:', menuId);
    
    document.getElementById('menuIdPrep').value = menuId;
    document.getElementById('nombrePreparacion').value = '';

    // Resetear y ocultar la sección de copia
    document.getElementById('opcionesCopiaContainer').style.display = 'none';
    document.getElementById('selectPreparacionCopia').innerHTML = '';

    if (componentesAlimentos.length === 0) {
        await cargarComponentesAlimentos();
    }

    const selectComponente = document.getElementById('componenteAlimento');
    selectComponente.innerHTML = '<option value="">Seleccione un componente...</option>';

    componentesAlimentos.forEach(comp => {
        const option = document.createElement('option');
        option.value = comp.id_componente;
        option.textContent = `${comp.componente} (${comp.id_grupo_alimentos__grupo_alimentos})`;
        selectComponente.appendChild(option);
    });

    console.log('✅ Abriendo modal Nueva Preparación');
    document.getElementById('modalNuevaPreparacion').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', function() {
    // Evento para mostrar las opciones de copia
    document.getElementById('btnMostrarOpcionesCopia').addEventListener('click', async function(e) {
        e.preventDefault();
        if (!modalidadActualId) {
            alert('No se pudo determinar la modalidad actual.');
            return;
        }

        try {
            const response = await fetch(`/nutricion/api/preparaciones-por-modalidad/${modalidadActualId}/`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const select = document.getElementById('selectPreparacionCopia');
            select.innerHTML = '<option value="">-- Seleccione una preparación --</option>';
            data.preparaciones.forEach(prep => {
                const option = new Option(prep.nombre, prep.id);
                select.add(option);
            });

            document.getElementById('opcionesCopiaContainer').style.display = 'block';

        } catch (error) {
            alert(`Error al cargar preparaciones para copiar: ${error.message}`);
        }
    });

    // Evento para ejecutar la copia
    document.getElementById('btnEjecutarCopia').addEventListener('click', async function() {
        const sourceId = document.getElementById('selectPreparacionCopia').value;
        const targetMenuId = document.getElementById('menuIdPrep').value;

        if (!sourceId) {
            alert('Por favor, seleccione una preparación para copiar.');
            return;
        }

        try {
            const response = await fetch('/nutricion/api/preparaciones/copiar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    source_preparacion_id: sourceId,
                    target_menu_id: targetMenuId
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ ${data.message}`);
                document.getElementById('modalNuevaPreparacion').style.display = 'none';
                cargarPreparacionesMenu(targetMenuId);
            } else {
                throw new Error(data.error || 'Error desconocido al copiar.');
            }

        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
});

async function cargarComponentesAlimentos() {
    try {
        const response = await fetch('/nutricion/api/componentes-alimentos/');
        const data = await response.json();
        if (data.componentes) {
            componentesAlimentos = data.componentes;
        }
    } catch (error) {
        console.error('Error al cargar componentes:', error);
        alert('Error al cargar componentes de alimentos');
    }
}
document.addEventListener('DOMContentLoaded', function() {
    const formNuevaPrep = document.getElementById('formNuevaPreparacion');
    if (formNuevaPrep) {
        formNuevaPrep.addEventListener('submit', async function(e) {
            e.preventDefault();
            const menuId = document.getElementById('menuIdPrep').value;
            const nombrePrep = document.getElementById('nombrePreparacion').value.trim();
            const componenteId = document.getElementById('componenteAlimento').value;

            if (!nombrePrep) {
                alert('Por favor ingrese un nombre para la preparación');
                return;
            }

            if (!componenteId) {
                alert('Por favor seleccione un componente de alimento');
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
                        preparacion: nombrePrep,
                        id_componente: componenteId
                    })
                });
                const data = await response.json();
                if (data.success || data.id_preparacion) {
                    alert(`✓ Preparación "${nombrePrep}" creada exitosamente`);
                    document.getElementById('modalNuevaPreparacion').style.display = 'none';
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
            for (const prep of data.preparaciones) {
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
    header.addEventListener('click', function(e) {
        if (!e.target.closest('.btn-delete')) {
            togglePreparacionAccordion(this);
        }
    });
    const btnDelete = header.querySelector('.btn-delete');
    btnDelete.addEventListener('click', function(e) {
        e.stopPropagation();
        eliminarPreparacion(preparacion.id_preparacion, menuId);
    });
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
    document.querySelectorAll('.preparacion-accordion-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.preparacion-accordion-header').forEach(h => h.classList.remove('active'));
    if (!isActive) {
        content.classList.add('active');
        header.classList.add('active');
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
let ingredientesSiesa = [];
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
// Sobrescribir con implementación completa
window.agregarFilaIngrediente = function() {
    const tbody = document.getElementById('tbodyIngredientes');
    const filaIndex = tbody.children.length;
    const tr = document.createElement('tr');
    tr.className = 'fila-ingrediente';
    tr.id = `fila-ing-${filaIndex}`;
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
};

// Sobrescribir con implementación completa
window.eliminarFilaIngrediente = function(index) {
    $(`#ingrediente-${index}`).select2('destroy');

    const fila = document.getElementById(`fila-ing-${index}`);
    if (fila) {
        fila.remove();
    }
};

// Sobrescribir con implementación completa
window.guardarIngredientes = async function() {
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
};

// Sobrescribir con implementación completa
window.cerrarModalIngredientes = function() {
    $('.select-ingrediente').each(function() {
        if ($(this).hasClass('select2-hidden-accessible')) {
            $(this).select2('destroy');
        }
    });

    document.getElementById('modalAgregarIngredientes').style.display = 'none';
    document.getElementById('tbodyIngredientes').innerHTML = '';
};

// Sobrescribir con implementación completa
window.cerrarModalPreparacion = function() {
    document.getElementById('modalNuevaPreparacion').style.display = 'none';
    const nombrePrep = document.getElementById('nombrePreparacion');
    const componenteAlim = document.getElementById('componenteAlimento');
    const menuIdPrep = document.getElementById('menuIdPrep');
    
    if (nombrePrep) nombrePrep.value = '';
    if (componenteAlim) componenteAlim.value = '';
    if (menuIdPrep) menuIdPrep.value = '';
};

// Sobrescribir con implementación completa
window.eliminarIngrediente = async function(preparacionId, ingredienteId) {
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
};
function resetearFiltros() {
    document.getElementById('filtroPrograma').innerHTML = '<option value="">Primero seleccione un municipio...</option>';
    document.getElementById('filtroPrograma').disabled = true;
    document.getElementById('btnAplicarFiltros').disabled = true;
    document.getElementById('infoProgramaContainer').style.display = 'none';
    document.getElementById('modalidadesContainer').innerHTML = '';
    document.getElementById('mensajeInicial').style.display = 'block';
}
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('close') && event.target.closest('.modal')) {
        event.target.closest('.modal').style.display = 'none';
    }

    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});
function abrirModalMenuEspecial(modalidadId) {
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
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudo crear el menú especial'));
        }
    } catch (error) {
        alert('Error al crear menú especial');
    }
}
function abrirEditarMenuEspecial(menuId, nombreActual) {
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
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudo eliminar el menú'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el menú especial');
    }
}

let menuActualAnalisis = null;

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
    const modal = document.getElementById('modalAnalisisNutricional');
    modal.style.display = 'block';

    const menuNumero = document.getElementById('menuNumeroModal').textContent;
    document.getElementById('menuNombreAnalisis').textContent = menuNumero;

    cargarAnalisisNutricional(menuId);
}

async function cargarAnalisisNutricional(menuId) {
    try {
        const contenidoAnalisis = document.getElementById('contenidoAnalisis');

        contenidoAnalisis.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin fa-3x"></i><p>Calculando análisis nutricional...</p></div>';

        const response = await fetch(`/nutricion/api/menus/${menuId}/analisis-nutricional/`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Error al cargar análisis');
        }

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

// Sobrescribir con implementación completa
window.cerrarModalAnalisisNutricional = function() {
    document.getElementById('modalAnalisisNutricional').style.display = 'none';
};

function renderizarAnalisisNutricional(data) {
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
    
    window.requerimientosNiveles = {};
    analisis_por_nivel.forEach((nivel, index) => {
        window.requerimientosNiveles[index] = nivel.requerimientos;
    });

    contenidoAnalisis.innerHTML = `
        <div class="menu-info-header">
            <h4><i class="fas fa-utensils"></i> ${menu.nombre}</h4>
            <div class="menu-details">
                <span class="badge badge-primary">Programa: ${menu.programa}</span>
                <span class="badge badge-secondary">Modalidad: ${menu.modalidad}</span>
            </div>
        </div>
        
        <div class="analisis-niveles-container">
            <h5><i class="fas fa-graduation-cap"></i> Análisis por Nivel Escolar</h5>
            <div class="niveles-accordion" id="nivelesAccordion">
                ${analisis_por_nivel.map((nivel, index) => crearAccordionNivelEscolar(nivel, index)).join('')}
            </div>
        </div>
    `;
    
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

function crearAccordionNivelEscolar(nivel, index) {
    const cardId = `collapse-${index}`;
    const isOpen = nivel.es_programa_actual;

    return `
        <div class="card nivel-card">
            <div class="card-header" id="heading-${index}">
                <h6 class="mb-0">
                    <button class="btn btn-link nivel-header-btn ${isOpen ? '' : 'collapsed'}" type="button" 
                            data-target="#${cardId}" 
                            aria-expanded="${isOpen ? 'true' : 'false'}" aria-controls="${cardId}">
                        <i class="fas fa-graduation-cap"></i>
                        ${nivel.nivel_escolar.nombre}
                        <div class="nivel-summary">
                            <span class="badge badge-primary">${nivel.totales.calorias_kcal.toFixed(0)} Kcal</span>
                            <span class="badge badge-success">${nivel.totales.peso_neto_total.toFixed(0)}g neto</span>
                            <span class="badge badge-warning">${nivel.totales.peso_bruto_total.toFixed(0)}g bruto</span>
                        </div>
                        <i class="fas fa-chevron-down toggle-icon" style="transform: ${isOpen ? 'rotate(180deg)' : 'rotate(0deg)'}"></i>
                    </button>
                </h6>
            </div>
            
            <div id="${cardId}" class="collapse ${isOpen ? 'show' : ''}" 
                 aria-labelledby="heading-${index}" data-parent="#nivelesAccordion">
                <div class="card-body">
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
    const pesoNeto = ingrediente.peso_neto_base;
    let nutrientesFinales;
    let baseNutrientesPor100g;

    if (ingrediente.valores_finales_guardados && pesoNeto > 0) {
        // Use the final, saved values directly for display
        nutrientesFinales = ingrediente.valores_finales_guardados;
        
        // Back-calculate the "per 100g" values to populate the data-* attributes correctly
        baseNutrientesPor100g = {
            calorias_kcal: (nutrientesFinales.calorias / pesoNeto) * 100,
            proteina_g: (nutrientesFinales.proteina / pesoNeto) * 100,
            grasa_g: (nutrientesFinales.grasa / pesoNeto) * 100,
            cho_g: (nutrientesFinales.cho / pesoNeto) * 100,
            calcio_mg: (nutrientesFinales.calcio / pesoNeto) * 100,
            hierro_mg: (nutrientesFinales.hierro / pesoNeto) * 100,
            sodio_mg: (nutrientesFinales.sodio / pesoNeto) * 100,
        };
    } else {
        // Fallback to using ICBF data if no saved values or peso is zero
        baseNutrientesPor100g = ingrediente.valores_por_100g;
        const factor = pesoNeto / 100;
        nutrientesFinales = {
            calorias: baseNutrientesPor100g.calorias_kcal * factor,
            proteina: baseNutrientesPor100g.proteina_g * factor,
            grasa: baseNutrientesPor100g.grasa_g * factor,
            cho: baseNutrientesPor100g.cho_g * factor,
            calcio: baseNutrientesPor100g.calcio_mg * factor,
            hierro: baseNutrientesPor100g.hierro_mg * factor,
            sodio: baseNutrientesPor100g.sodio_mg * factor,
        };
    }

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
                       data-calorias="${baseNutrientesPor100g.calorias_kcal}"
                       data-proteina="${baseNutrientesPor100g.proteina_g}"
                       data-grasa="${baseNutrientesPor100g.grasa_g}"
                       data-cho="${baseNutrientesPor100g.cho_g}"
                       data-calcio="${baseNutrientesPor100g.calcio_mg}"
                       data-hierro="${baseNutrientesPor100g.hierro_mg}"
                       data-sodio="${baseNutrientesPor100g.sodio_mg}"
                       data-prep-id="${ingrediente.id_preparacion_real || prepIndex}"
                       data-ing-id="${ingrediente.id_ingrediente || ingrediente.id_ingrediente_siesa || ingIndex}">
            </td>
            <td class="peso-bruto-calc" id="bruto-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${ingrediente.peso_bruto_base.toFixed(0)}
            </td>
            <td class="parte-comestible">${ingrediente.parte_comestible}%</td>
            <td class="nutriente-cal" id="cal-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.calorias.toFixed(1)}
            </td>
            <td class="nutriente-prot" id="prot-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.proteina.toFixed(1)}
            </td>
            <td class="nutriente-grasa" id="grasa-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.grasa.toFixed(1)}
            </td>
            <td class="nutriente-cho" id="cho-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.cho.toFixed(1)}
            </td>
            <td class="nutriente-calcio" id="calcio-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.calcio.toFixed(1)}
            </td>
            <td class="nutriente-hierro" id="hierro-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.hierro.toFixed(1)}
            </td>
            <td class="nutriente-sodio" id="sodio-${nivelIndex}-${prepIndex}-${ingIndex}">
                ${nutrientesFinales.sodio.toFixed(1)}
            </td>
        </tr>
    `;
}

function inicializarEventosInputs() {
    let actualizandoPorPeso = false;
    let actualizandoPorPorcentaje = false;
    
    $(document).on('input change', '.peso-input', function() {
        if (actualizandoPorPorcentaje) return;

        actualizandoPorPeso = true;

        const input = $(this);
        const nivelIndex = input.closest('.ingrediente-row').data('nivel');
        const prepIndex = input.closest('.ingrediente-row').data('prep');
        const ingIndex = input.closest('.ingrediente-row').data('ing');

        const pesoNeto = Math.max(0, parseFloat(input.val()) || 0);
        const parteComestible = parseFloat(input.data('parte-comestible')) || 100;
        const caloriasPor100g = parseFloat(input.data('calorias')) || 0;
        const proteinaPor100g = parseFloat(input.data('proteina')) || 0;
        const grasaPor100g = parseFloat(input.data('grasa')) || 0;
        const choPor100g = parseFloat(input.data('cho')) || 0;
        const calcioPor100g = parseFloat(input.data('calcio')) || 0;
        const hierroPor100g = parseFloat(input.data('hierro')) || 0;
        const sodioPor100g = parseFloat(input.data('sodio')) || 0;

        const pesoBruto = parteComestible > 0 ? (pesoNeto * 100) / parteComestible : pesoNeto;

        const factor = pesoNeto / 100;
        const calorias = caloriasPor100g * factor;
        const proteina = proteinaPor100g * factor;
        const grasa = grasaPor100g * factor;
        const cho = choPor100g * factor;
        const calcio = calcioPor100g * factor;
        const hierro = hierroPor100g * factor;
        const sodio = sodioPor100g * factor;

        $(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text(pesoBruto.toFixed(0));

        $(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text(calorias.toFixed(1));
        $(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text(proteina.toFixed(1));
        $(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text(grasa.toFixed(1));
        $(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text(cho.toFixed(1));
        $(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text(calcio.toFixed(1));
        $(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text(hierro.toFixed(1));
        $(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text(sodio.toFixed(1));

        recalcularTotalesNivel(nivelIndex);

        actualizandoPorPeso = false;
    });
    
    let timeoutPorcentaje = null;

    $(document).on('change', '.porcentaje-input', function() {
        if (actualizandoPorPeso) return;

        const input = $(this);
        const nivelIndex = input.data('nivel');
        const nutriente = input.data('nutriente');
        const porcentajeDeseado = parseFloat(input.val()) || 0;

        if (porcentajeDeseado < 0) {
            input.val(0);
            return;
        }
        if (porcentajeDeseado > 100) {
            input.val(100);
            return;
        }

        clearTimeout(timeoutPorcentaje);
        timeoutPorcentaje = setTimeout(() => {
            actualizandoPorPorcentaje = true;

            console.log('Editando porcentaje:', { nivelIndex, nutriente, porcentajeDeseado });

            calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado);

            actualizandoPorPorcentaje = false;
        }, 300);
    });
    
    $(document).on('click', '.nivel-header-btn', function(e) {
        e.preventDefault();
        const button = $(this);
        const targetId = button.data('target');
        const target = $(targetId);
        const icon = button.find('.toggle-icon');

        if (target.hasClass('show')) {
            target.removeClass('show');
            button.attr('aria-expanded', 'false').addClass('collapsed');
            icon.css('transform', 'rotate(0deg)');
        } else {
            $('.nivel-card .collapse.show').each(function() {
                const otherCollapse = $(this);
                const otherButton = $(`[data-target="#${otherCollapse.attr('id')}"]`);
                const otherIcon = otherButton.find('.toggle-icon');

                otherCollapse.removeClass('show');
                otherButton.attr('aria-expanded', 'false').addClass('collapsed');
                otherIcon.css('transform', 'rotate(0deg)');
            });

            target.addClass('show');
            button.attr('aria-expanded', 'true').removeClass('collapsed');
            icon.css('transform', 'rotate(180deg)');
        }
    });
}

// =================== FUNCIONES DE CÁLCULO Y GUARDADO ===================

// Las siguientes funciones están expuestas globalmente desde los módulos:
// - recalcularTotalesNivel()
// - calcularPesosDesdeAdecuacion()
// - recalcularPorcentajesAdecuacion()
// - getEstadoAdecuacion()
// - guardarAnalisisAutomatico()

// =================== EXPORTAR FUNCIONES GLOBALES ===================
// ✅ TODAS las funciones ya están exportadas como window.* en sus definiciones
// Este bloque ya no es necesario porque usamos el patrón de sobrescritura:
// 
// 1. Declaración temprana (líneas 14-59) con implementación básica
// 2. Sobrescritura completa (líneas 685-859) con lógica completa
// 
// Funciones disponibles globalmente:
// - window.cerrarModalPreparacion
// - window.cerrarModalIngredientes
// - window.cerrarModalAnalisisNutricional
// - window.abrirAgregarIngrediente
// - window.agregarFilaIngrediente
// - window.guardarIngredientes
// - window.eliminarIngrediente
// - window.eliminarFilaIngrediente