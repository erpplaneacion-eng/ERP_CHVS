/**
 * ciclos_menus.js
 * Lógica para la página de Planificación de Ciclos de Menús.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Obtener elementos del DOM
    const btnBuscar = document.getElementById('btn-buscar');
    const btnInicializar = document.getElementById('btn-inicializar');
    const etcSelect = document.getElementById('filter-etc');
    const focalizacionSelect = document.getElementById('filter-focalizacion');
    const anoInput = document.getElementById('filter-ano');
    const resultsContainer = document.getElementById('results-container');

    // Configuración desde el template de Django
    const config = window.CICLOS_MENUS_CONFIG || {};

    // Verificación de dependencias críticas
    if (typeof ERPUtils === 'undefined') {
        console.error('❌ ERPUtils no está disponible');
    }

    // Verificación y configuración de ERPUtils
    if (typeof ERPUtils === 'undefined') {
        window.ERPUtils = {
            showAlert: function(message, type) {
                alert(message);
            },
            showNotification: function(message, type) {
                console.log(`NOTIFICATION [${type}]: ${message}`);
            },
            showConfirm: function(title, text, icon) {
                return Promise.resolve(confirm(`${title}\n\n${text}`));
            }
        };
    } else {
        if (typeof ERPUtils.showConfirm !== 'function') {
            ERPUtils.showConfirm = function(title, text, icon) {
                return Promise.resolve(confirm(`${title}\n\n${text}`));
            };
        }
        if (typeof ERPUtils.showNotification !== 'function') {
            ERPUtils.showNotification = function(message, type) {
                console.log(`NOTIFICATION [${type}]: ${message}`);
            };
        }
    }

    // =================================================================
    // EVENT LISTENERS
    // =================================================================

    // Evento para el botón de Buscar
    if (btnBuscar) {
        btnBuscar.addEventListener('click', function() {
            const etc = etcSelect.value;
            const focalizacion = focalizacionSelect.value;
            const ano = anoInput.value;

            if (!etc || !focalizacion) {
                mostrarAlertaSegura('Por favor, seleccione un ETC y una Focalización.', 'warning');
                return;
            }

            buscarDatos(etc, focalizacion, ano);
        });
    }

    // Evento para el botón de Inicializar
    if (btnInicializar) {
        btnInicializar.addEventListener('click', function() {
            const etc = etcSelect.value;
            const focalizacion = focalizacionSelect.value;
            const ano = anoInput.value;

            if (!etc || !focalizacion) {
                mostrarAlertaSegura('Por favor, seleccione un ETC y una Focalización.', 'warning');
                return;
            }

            // Inicia el proceso. El primer llamado nunca se fuerza.
            inicializarCiclos(etc, focalizacion, ano, false);
        });
    }

    async function buscarDatos(etc, focalizacion, ano) {
        mostrarCargando();

        try {
            const url = `${config.urlObtener}?etc=${encodeURIComponent(etc)}&focalizacion=${encodeURIComponent(focalizacion)}&ano=${ano}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                if (data.datos && data.datos.length > 0) {
                    renderizarTabla(data.datos);
                } else {
                    resultsContainer.innerHTML = `
                        <div class="no-data">
                            <i class="fas fa-info-circle"></i>
                            <p>No se encontraron datos de planificación. Use "Inicializar desde Listados" para crear los registros.</p>
                        </div>
                    `;
                }
            } else {
                mostrarAlertaSegura(data.error || 'Error al obtener datos', 'error');
                resultsContainer.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Error al cargar datos</p>
                    </div>
                `;
            }
        } catch (error) {
            mostrarAlertaSegura('Error de conexión al servidor', 'error');
            resultsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error de conexión</p>
                </div>
            `;
        }
    }

    async function inicializarCiclos(etc, focalizacion, ano, forzar) {
        // Mostrar indicador de carga
        btnInicializar.disabled = true;
        btnInicializar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

        try {
            const response = await fetch(config.urlInicializar, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': config.csrfToken
                },
                body: JSON.stringify({
                    etc: etc,
                    focalizacion: focalizacion,
                    ano: parseInt(ano),
                    forzar_actualizacion: forzar
                })
            });

            const data = await response.json();

            if (response.ok) {
                if (data.success) {
                    mostrarNotificacionSegura(data.message, 'success');
                    // Renderizar la tabla con los datos recibidos
                    renderizarTabla(data.datos);

                } else if (data.requiere_confirmacion) {
                    if (typeof ERPUtils === 'undefined' || typeof ERPUtils.showConfirm !== 'function') {
                        await mostrarConfirmacionNativa(data, etc, focalizacion, ano);
                        return;
                    }

                    // Verificar que SweetAlert2 esté disponible
                    if (typeof Swal === 'undefined') {
                        await mostrarConfirmacionNativa(data, etc, focalizacion, ano);
                        return;
                    }

                    // Usar SweetAlert2 si está disponible, sino modal personalizado
                    if (typeof Swal !== 'undefined') {
                        const userConfirmed = await ERPUtils.showConfirm(
                            'Confirmación Requerida',
                            `${data.warning}. Existen ${data.total_registros_existentes} registros que serán sobreescritos. ¿Desea continuar?`,
                            'warning'
                        );

                        if (userConfirmed) {
                            inicializarCiclos(etc, focalizacion, ano, true);
                        } else {
                            mostrarNotificacionSegura('Operación cancelada. Los registros existentes se mantienen intactos.', 'info');
                            buscarDatos(etc, focalizacion, ano);
                        }
                    } else {
                        await mostrarConfirmacionNativa(data, etc, focalizacion, ano);
                    }
                } else {
                    // Otros errores controlados por el backend
                    mostrarAlertaSegura(data.error || 'Ocurrió un error inesperado.', 'error');
                }
            } else {
                // Errores de servidor (500, etc.)
                const errorMsg = data.error || 'Error desconocido del servidor';
                mostrarAlertaSegura(`Error del servidor: ${errorMsg}`, 'error');
            }

        } catch (error) {
            mostrarAlertaSegura('Error de red. Por favor, intente de nuevo.', 'error');
        } finally {
            // Reactivar botón
            btnInicializar.disabled = false;
            btnInicializar.innerHTML = '<i class="fas fa-sync-alt"></i> Inicializar desde Listados';
        }
    }

    function renderizarTabla(sedes) {
        if (!sedes || sedes.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-info-circle"></i>
                    <p>No hay datos disponibles</p>
                </div>
            `;
            return;
        }

        let html = '';

        sedes.forEach((sedeData, index) => {
            // Calcular totales para el resumen
            let totalCapAm = 0;
            let totalCapPm = 0;
            let totalAlmuerzo = 0;
            let totalRefuerzo = 0;
            let totalGeneral = 0;

            sedeData.niveles.forEach(nivel => {
                totalCapAm += nivel.cap_am;
                totalCapPm += nivel.cap_pm;
                totalAlmuerzo += nivel.almuerzo_ju;
                totalRefuerzo += nivel.refuerzo;
                totalGeneral += nivel.total;
            });

            html += `
                <div class="sede-card">
                    <div class="sede-header collapsed" data-sede-index="${index}">
                        <div class="sede-info">
                            <div>
                                <i class="fas fa-school"></i> ${sedeData.sede}
                            </div>
                            <div class="sede-summary">
                                <span title="Total de raciones">${totalGeneral} raciones</span>
                            </div>
                        </div>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="sede-body collapsed">
                        <table class="sede-table">
                            <thead>
                                <tr>
                                    <th>Nivel Escolar</th>
                                    <th>Grados</th>
                                    <th>CAP AM</th>
                                    <th>CAP PM</th>
                                    <th>Almuerzo JU</th>
                                    <th>Refuerzo</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            sedeData.niveles.forEach(nivel => {
                html += `
                    <tr>
                        <td><strong>${nivel.nivel_escolar}</strong></td>
                        <td class="grados-cell">${nivel.grados || 'N/A'}</td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="cap_am">
                            <span class="value">${nivel.cap_am}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="cap_pm">
                            <span class="value">${nivel.cap_pm}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="almuerzo_ju">
                            <span class="value">${nivel.almuerzo_ju}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="refuerzo">
                            <span class="value">${nivel.refuerzo}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td><strong>${nivel.total}</strong></td>
                    </tr>
                `;
            });

            // Fila de totales
            html += `
                    <tr class="total-row">
                        <td colspan="2"><strong>TOTAL SEDE</strong></td>
                        <td><strong>${totalCapAm}</strong></td>
                        <td><strong>${totalCapPm}</strong></td>
                        <td><strong>${totalAlmuerzo}</strong></td>
                        <td><strong>${totalRefuerzo}</strong></td>
                        <td><strong>${totalGeneral}</strong></td>
                    </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = html;

        // Agregar event listeners
        agregarListenersAcordeon();
        agregarListenersEdicion();
    }

    function agregarListenersAcordeon() {
        const headers = document.querySelectorAll('.sede-header');

        headers.forEach(header => {
            header.addEventListener('click', function() {
                const body = this.nextElementSibling;

                // Toggle classes
                this.classList.toggle('collapsed');
                body.classList.toggle('collapsed');
            });
        });
    }

    function agregarListenersEdicion() {
        const editableCells = document.querySelectorAll('.editable-cell');

        editableCells.forEach(cell => {
            cell.addEventListener('click', function(e) {
                // Evitar que el click se propague al header del acordeón
                e.stopPropagation();
                hacerEditable(this);
            });
        });
    }

    function hacerEditable(cell) {
        if (cell.querySelector('input')) {
            return; // Ya está en modo edición
        }

        const valueSpan = cell.querySelector('.value');
        const currentValue = valueSpan.textContent.trim();
        const id = cell.dataset.id;
        const campo = cell.dataset.campo;

        // Crear input
        const input = document.createElement('input');
        input.type = 'number';
        input.min = '0';
        input.value = currentValue;
        input.style.width = '60px';

        // Reemplazar el contenido
        cell.innerHTML = '';
        cell.appendChild(input);
        input.focus();
        input.select();

        // Guardar al presionar Enter o perder foco
        const saveValue = async () => {
            const newValue = input.value.trim();

            if (newValue === currentValue) {
                // No hubo cambios
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                return;
            }

            if (!newValue || newValue < 0) {
                mostrarAlertaSegura('Valor inválido', 'error');
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                return;
            }

            // Guardar en servidor
            try {
                const response = await fetch(config.urlActualizar, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': config.csrfToken
                    },
                    body: JSON.stringify({
                        id: id,
                        campo: campo,
                        valor: parseInt(newValue)
                    })
                });

                const data = await response.json();

                if (data.success) {
                    cell.innerHTML = `<span class="value">${newValue}</span><i class="fas fa-edit edit-icon"></i>`;
                    mostrarNotificacionSegura('Valor actualizado exitosamente', 'success');

                    // Actualizar totales
                    actualizarTotales(cell.closest('table'));
                } else {
                    mostrarAlertaSegura(data.error || 'Error al actualizar', 'error');
                    cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                }
            } catch (error) {
                mostrarAlertaSegura('Error de conexión al servidor', 'error');
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
            }
        };

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveValue();
            }
        });

        input.addEventListener('blur', saveValue);
    }

    function actualizarTotales(table) {
        const rows = table.querySelectorAll('tbody tr:not(.total-row)');
        let totalCapAm = 0;
        let totalCapPm = 0;
        let totalAlmuerzo = 0;
        let totalRefuerzo = 0;

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                totalCapAm += parseInt(cells[2].querySelector('.value')?.textContent || 0);
                totalCapPm += parseInt(cells[3].querySelector('.value')?.textContent || 0);
                totalAlmuerzo += parseInt(cells[4].querySelector('.value')?.textContent || 0);
                totalRefuerzo += parseInt(cells[5].querySelector('.value')?.textContent || 0);

                // Actualizar total de la fila
                const rowTotal =
                    parseInt(cells[2].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[3].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[4].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[5].querySelector('.value')?.textContent || 0);
                cells[6].innerHTML = `<strong>${rowTotal}</strong>`;
            }
        });

        const totalGeneral = totalCapAm + totalCapPm + totalAlmuerzo + totalRefuerzo;

        // Actualizar fila de totales
        const totalRow = table.querySelector('.total-row');
        if (totalRow) {
            const totalCells = totalRow.querySelectorAll('td');
            totalCells[1].innerHTML = `<strong>${totalCapAm}</strong>`;
            totalCells[2].innerHTML = `<strong>${totalCapPm}</strong>`;
            totalCells[3].innerHTML = `<strong>${totalAlmuerzo}</strong>`;
            totalCells[4].innerHTML = `<strong>${totalRefuerzo}</strong>`;
            totalCells[5].innerHTML = `<strong>${totalGeneral}</strong>`;
        }

        // Actualizar resumen en el header
        const sedeCard = table.closest('.sede-card');
        if (sedeCard) {
            const summary = sedeCard.querySelector('.sede-summary span');
            if (summary) {
                summary.textContent = `${totalGeneral} raciones`;
            }
        }
    }

    function mostrarCargando() {
        resultsContainer.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Cargando datos...</p>
            </div>
        `;
    }


    function mostrarAlertaSegura(message, type = 'info') {
        if (typeof ERPUtils !== 'undefined' && typeof ERPUtils.showAlert === 'function') {
            ERPUtils.showAlert(message, type);
        } else {
            alert(message);
        }
    }

    function mostrarNotificacionSegura(message, type = 'info') {
        if (typeof ERPUtils !== 'undefined' && typeof ERPUtils.showNotification === 'function') {
            ERPUtils.showNotification(message, type);
        } else {
            console.log(`NOTIFICATION [${type}]: ${message}`);
        }
    }

    function mostrarConfirmacionSegura(title, text, icon = 'warning') {
        if (typeof ERPUtils !== 'undefined' && typeof ERPUtils.showConfirm === 'function') {
            return ERPUtils.showConfirm(title, text, icon);
        } else {
            return mostrarModalConfirmacionPersonalizado(title, text, icon);
        }
    }

    function mostrarModalConfirmacionPersonalizado(title, message, type = 'warning') {
        console.log('🔍 DEBUG: Iniciando creación de modal personalizado');

        return new Promise((resolve) => {
            // Crear modal si no existe
            let modal = document.getElementById('custom-confirm-modal');
            if (!modal) {
                console.log('🔍 DEBUG: Modal no existe, creando nuevo modal...');
                modal = document.createElement('div');
                modal.id = 'custom-confirm-modal';
                modal.className = 'custom-modal-overlay';
                modal.innerHTML = `
                    <div class="custom-modal-content">
                        <div class="custom-modal-header">
                            <h3 class="custom-modal-title"></h3>
                            <button class="custom-modal-close">&times;</button>
                        </div>
                        <div class="custom-modal-body">
                            <div class="custom-modal-icon"></div>
                            <p class="custom-modal-message"></p>
                        </div>
                        <div class="custom-modal-footer">
                            <button class="custom-btn custom-btn-cancel">Cancelar</button>
                            <button class="custom-btn custom-btn-confirm">Continuar</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                console.log('🔍 DEBUG: Modal creado y agregado al DOM');
            } else {
                console.log('🔍 DEBUG: Modal ya existe, reutilizando');
                // Limpiar event listeners anteriores para evitar duplicados
                const newModal = modal.cloneNode(true);
                modal.parentNode.replaceChild(newModal, modal);
                modal = newModal;
                modal.id = 'custom-confirm-modal';
                console.log('🔍 DEBUG: Modal limpiado y reutilizado');
            }

            // Configurar contenido según el tipo
            const config = getConfiguracionModal(type);
            console.log('🔍 DEBUG: Configuración del modal:', config);

            try {
                // Configurar contenido
                modal.querySelector('.custom-modal-title').textContent = title;
                modal.querySelector('.custom-modal-message').innerHTML = message;
                modal.querySelector('.custom-modal-icon').innerHTML = `<i class="${config.icon}"></i>`;
                modal.querySelector('.custom-modal-header').style.backgroundColor = config.headerColor;
                modal.querySelector('.custom-btn-confirm').style.backgroundColor = config.buttonColor;
                modal.querySelector('.custom-btn-confirm').innerHTML = `<i class="${config.buttonIcon}"></i> ${config.buttonText}`;

                console.log('🔍 DEBUG: Contenido del modal configurado');

                // Función para manejar la resolución
                const handleResolve = (result) => {
                    console.log('🔍 DEBUG: Resolviendo modal con resultado:', result);
                    modal.style.display = 'none';
                    modal.querySelector('.custom-modal-content').style.animation = 'modalSlideOut 0.3s ease-in';
                    setTimeout(() => {
                        resolve(result);
                    }, 300);
                };

                // Event listeners con debugging
                const closeBtn = modal.querySelector('.custom-modal-close');
                const cancelBtn = modal.querySelector('.custom-btn-cancel');
                const confirmBtn = modal.querySelector('.custom-btn-confirm');

                console.log('🔍 DEBUG: Elementos del modal encontrados:', {
                    closeBtn: !!closeBtn,
                    cancelBtn: !!cancelBtn,
                    confirmBtn: !!confirmBtn
                });

                closeBtn.addEventListener('click', (e) => {
                    console.log('🔍 DEBUG: Usuario hizo clic en cerrar modal');
                    e.stopPropagation();
                    handleResolve(false);
                });

                cancelBtn.addEventListener('click', (e) => {
                    console.log('🔍 DEBUG: Usuario hizo clic en Cancelar');
                    e.stopPropagation();
                    handleResolve(false);
                });

                confirmBtn.addEventListener('click', (e) => {
                    console.log('🔍 DEBUG: Usuario hizo clic en Continuar');
                    e.stopPropagation();
                    handleResolve(true);
                });

                // Cerrar al hacer clic fuera del modal
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        console.log('🔍 DEBUG: Usuario hizo clic fuera del modal');
                        handleResolve(false);
                    }
                });

                // Mostrar modal SIN animación inicial para evitar conflictos
                modal.style.display = 'flex';
                modal.querySelector('.custom-modal-content').style.transform = 'scale(1)';
                modal.querySelector('.custom-modal-content').style.opacity = '1';

                console.log('🔍 DEBUG: Modal mostrado en pantalla');

                // Auto-focus en el botón de confirmar después de un breve delay
                setTimeout(() => {
                    const confirmBtn = modal.querySelector('.custom-btn-confirm');
                    if (confirmBtn) {
                        confirmBtn.focus();
                        console.log('🔍 DEBUG: Focus aplicado al botón Continuar');
                    } else {
                        console.error('🔍 DEBUG: No se pudo encontrar el botón de confirmar');
                    }
                }, 100);

            } catch (error) {
                console.error('❌ DEBUG: Error al configurar modal:', error);
                resolve(confirm(`${title}\n\n${message.replace(/<[^>]*>/g, '')}`));
            }
        });
    }

    function getConfiguracionModal(type) {
        const configs = {
            warning: {
                icon: 'fas fa-exclamation-triangle fa-3x',
                headerColor: '#f39c12',
                buttonColor: '#f39c12',
                buttonIcon: 'fas fa-exclamation-triangle',
                buttonText: 'Continuar'
            },
            error: {
                icon: 'fas fa-times-circle fa-3x',
                headerColor: '#e74c3c',
                buttonColor: '#e74c3c',
                buttonIcon: 'fas fa-times',
                buttonText: 'Aceptar'
            },
            info: {
                icon: 'fas fa-info-circle fa-3x',
                headerColor: '#3498db',
                buttonColor: '#3498db',
                buttonIcon: 'fas fa-check',
                buttonText: 'Entendido'
            },
            success: {
                icon: 'fas fa-check-circle fa-3x',
                headerColor: '#27ae60',
                buttonColor: '#27ae60',
                buttonIcon: 'fas fa-check',
                buttonText: 'Aceptar'
            }
        };

        return configs[type] || configs.warning;
    }

    function cerrarModalPersonalizado(modal, result, resolve) {
        modal.style.display = 'none';
        modal.querySelector('.custom-modal-content').style.animation = 'modalSlideOut 0.3s ease-in';
        setTimeout(() => {
            resolve(result);
        }, 300);
    }


    async function mostrarConfirmacionNativa(data, etc, focalizacion, ano) {
        const titulo = '⚠️ Confirmación Requerida';
        const mensaje = `
            <div style="text-align: center; padding: 10px;">
                <strong style="color: #e74c3c; font-size: 16px; display: block; margin-bottom: 15px;">
                    ${data.warning}
                </strong>
                <div style="background-color: #fff3cd; border: 2px solid #f39c12; border-radius: 10px; padding: 15px; margin: 15px 0;">
                    <i class="fas fa-exclamation-triangle" style="color: #f39c12; font-size: 24px; margin-right: 10px;"></i>
                    <span style="color: #856404; font-weight: 600;">
                        Existen <strong style="color: #d68910;">${data.total_registros_existentes} registros</strong> que serán sobreescritos
                    </span>
                </div>
                <p style="color: #2c3e50; margin-top: 15px;">
                    ¿Está seguro de que desea continuar? Esta acción no se puede deshacer.
                </p>
            </div>
        `;

        try {
            const userConfirmed = await mostrarModalConfirmacionPersonalizado(titulo, mensaje, 'warning');

            if (userConfirmed) {
                inicializarCiclos(etc, focalizacion, ano, true);
            } else {
                mostrarNotificacionSegura('Operación cancelada. Los registros existentes se mantienen intactos.', 'info');
                buscarDatos(etc, focalizacion, ano);
            }

            return userConfirmed;
        } catch (error) {
            console.error('Error al mostrar modal personalizado:', error);
            const confirmacionNativa = confirm(`${titulo}\n\n${data.warning}. Existen ${data.total_registros_existentes} registros que serán sobreescritos. ¿Desea continuar?`);

            if (confirmacionNativa) {
                inicializarCiclos(etc, focalizacion, ano, true);
            } else {
                mostrarNotificacionSegura('Operación cancelada. Los registros existentes se mantienen intactos.', 'info');
                buscarDatos(etc, focalizacion, ano);
            }

            return confirmacionNativa;
        }
    }
});