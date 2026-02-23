/**
 * reportes_asistencia.js
 * Lógica de la página de generación de reportes de asistencia.
 * Incluye: gestión de pestañas, generación individual/masiva,
 *          generación prediligenciada y calendario picker de días.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ===== GESTIÓN DE PESTAÑAS =====
    const tabButtons  = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            const targetTab = this.dataset.tab;
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // ===== CALENDARIO PICKER DE DÍAS =====
    const MESES_NUM = {
        'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
        'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
        'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
    };
    const DIAS_SEMANA = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'];

    const calPopover    = document.getElementById('dias-calendar-popover');
    const calGridBody   = document.getElementById('cal-grid-body');
    const calMonthLabel = document.getElementById('cal-month-label');
    const calCountLabel = document.getElementById('cal-count-label');
    const calBtnClear   = document.getElementById('cal-btn-clear');

    let calActiveTarget        = null;
    let calActiveBtn           = null;
    let calModoPrediligenciada = false;
    let calSelectedDays        = new Set();
    const AÑO_ACTUAL    = new Date().getFullYear();

    function diasEnMes(mesNum, año) {
        return new Date(año, mesNum, 0).getDate();
    }

    // Lunes=0 … Domingo=6
    function primerDiaSemana(mesNum, año) {
        const d = new Date(año, mesNum - 1, 1).getDay();
        return d === 0 ? 6 : d - 1;
    }

    function renderCalendar(mesNombre, año) {
        const mesNum    = MESES_NUM[mesNombre] || 1;
        calMonthLabel.textContent = `${mesNombre} ${año}`;

        const totalDias = diasEnMes(mesNum, año);
        const offsetIni = primerDiaSemana(mesNum, año);
        const fragment  = document.createDocumentFragment();

        // Cabecera Lu…Do
        DIAS_SEMANA.forEach(d => {
            const h = document.createElement('div');
            h.className   = 'cal-day-header';
            h.textContent = d;
            fragment.appendChild(h);
        });

        // Celdas vacías iniciales
        for (let i = 0; i < offsetIni; i++) {
            const e = document.createElement('div');
            e.className = 'cal-day empty';
            fragment.appendChild(e);
        }

        // Días del mes
        for (let dia = 1; dia <= totalDias; dia++) {
            const cell = document.createElement('div');
            cell.className    = 'cal-day' + (calSelectedDays.has(dia) ? ' selected' : '');
            cell.textContent  = dia;
            cell.dataset.day  = dia;
            cell.addEventListener('click', function () {
                const d = parseInt(this.dataset.day);
                if (calSelectedDays.has(d)) {
                    calSelectedDays.delete(d);
                    this.classList.remove('selected');
                } else {
                    calSelectedDays.add(d);
                    this.classList.add('selected');
                }
                syncCalendarState();
            });
            fragment.appendChild(cell);
        }

        calGridBody.innerHTML = '';
        calGridBody.appendChild(fragment);
        syncCalendarState();
    }

    function syncCalendarState() {
        const count = calSelectedDays.size;
        calCountLabel.textContent = count === 0
            ? '0 días sel.'
            : `${count} día${count !== 1 ? 's' : ''} sel.`;

        if (!calActiveTarget || !calActiveBtn) return;

        const hiddenInput = document.getElementById(calActiveTarget);
        const labelSpan   = calActiveBtn.querySelector('.dias-label');
        const isBulk      = calActiveBtn.dataset.mesTarget === 'bulk-mes';

        if (count === 0) {
            hiddenInput.value = '';
            calActiveBtn.classList.remove('has-dias');
            if (labelSpan) labelSpan.textContent = isBulk
                ? 'Sin días (usa hábiles del mes)'
                : 'Sin días';
        } else {
            const sorted = Array.from(calSelectedDays).sort((a, b) => a - b);
            hiddenInput.value = sorted.join(',');
            calActiveBtn.classList.add('has-dias');
            if (labelSpan) {
                const preview = sorted.slice(0, 5).join(', ') + (sorted.length > 5 ? '…' : '');
                labelSpan.textContent = `${count} día${count !== 1 ? 's' : ''}: ${preview}`;
            }
        }
    }

    function openCalendar(btn) {
        const targetId    = btn.dataset.target;
        const mesTargetId = btn.dataset.mesTarget;
        const mesSelect   = document.getElementById(mesTargetId);
        const mesNombre   = mesSelect ? mesSelect.value : 'ENERO';

        calActiveTarget = targetId;
        calActiveBtn    = btn;

        // Restaurar días ya guardados en el hidden input
        const hiddenInput = document.getElementById(targetId);
        calSelectedDays   = new Set();
        if (hiddenInput && hiddenInput.value.trim()) {
            hiddenInput.value.split(',').forEach(v => {
                const n = parseInt(v.trim());
                if (!isNaN(n)) calSelectedDays.add(n);
            });
        }

        renderCalendar(mesNombre, AÑO_ACTUAL);

        // Posicionar: fixed → usar coordenadas de viewport (sin scrollY)
        calPopover.style.visibility = 'hidden';
        calPopover.style.display    = 'block';

        const rect  = btn.getBoundingClientRect();
        const popW  = calPopover.offsetWidth  || 280;
        const popH  = calPopover.offsetHeight || 300;
        const vpW   = window.innerWidth;
        const vpH   = window.innerHeight;

        // Horizontal: alinear con el botón sin salirse de la pantalla
        let left = rect.left;
        if (left + popW > vpW - 8) left = vpW - popW - 8;
        if (left < 8) left = 8;

        // Vertical: debajo del botón; si no cabe, abrir hacia arriba
        let top;
        if (rect.bottom + 6 + popH <= vpH) {
            top = rect.bottom + 6;
        } else {
            top = Math.max(8, rect.top - popH - 6);
        }

        calPopover.style.left       = left + 'px';
        calPopover.style.top        = top  + 'px';
        calPopover.style.visibility = 'visible';
    }

    function closeCalendar() {
        calPopover.style.display   = 'none';
        calActiveTarget            = null;
        calActiveBtn               = null;
        calModoPrediligenciada     = false;
    }

    // Clic en botón picker
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-dias-picker');
        if (btn) {
            e.stopPropagation();
            if (calPopover.style.display === 'block' && calActiveBtn === btn) {
                closeCalendar();
            } else {
                openCalendar(btn);
            }
            return;
        }
        // Clic fuera del popover
        if (calPopover && !calPopover.contains(e.target)) {
            closeCalendar();
        }
    });

    // Limpiar selección
    calBtnClear.addEventListener('click', function () {
        calSelectedDays.clear();
        calGridBody.querySelectorAll('.cal-day.selected')
            .forEach(c => c.classList.remove('selected'));
        syncCalendarState();
    });

    // Si cambia el mes mientras el popover está abierto, refrescar calendario
    document.addEventListener('change', function (e) {
        if (!e.target.id || calPopover.style.display !== 'block') return;
        // Modo normal (Tab 1): refrescar según data-mes-target del botón activo
        if (calActiveBtn && e.target.id === calActiveBtn.dataset.mesTarget) {
            calSelectedDays.clear();
            renderCalendar(e.target.value, AÑO_ACTUAL);
        }
        // Modo prediligenciada (Tab 2): refrescar al cambiar pred-mes
        if (calModoPrediligenciada && e.target.id === 'pred-mes') {
            calSelectedDays.clear();
            renderCalendar(e.target.value, AÑO_ACTUAL);
        }
    });

    // ===== TAB 2: GENERACIÓN PREDILIGENCIADA =====
    let conteoEstudiantes = {
        total: 0, preescolar: 0, primaria_1_3: 0,
        primaria_4_5: 0, secundaria: 0, media: 0
    };

    let configuracionDias = [];

    const predPrograma        = document.getElementById('pred-programa');
    const predSede            = document.getElementById('pred-sede');
    const predFocalizacion    = document.getElementById('pred-focalizacion');
    const predComplemento     = document.getElementById('pred-complemento');
    const btnCargarEstudiantes = document.getElementById('btn-cargar-estudiantes');

    if (predPrograma) {
        predPrograma.addEventListener('change', async function () {
            const programaId = this.value;
            predSede.disabled          = !programaId;
            predFocalizacion.disabled  = true;
            predComplemento.disabled   = true;
            btnCargarEstudiantes.disabled = true;

            if (!programaId) {
                predSede.innerHTML = '<option value="">-- Seleccione programa primero --</option>';
                return;
            }

            try {
                const response = await fetch(`/facturacion/api/get-sedes-completas/?programa_id=${programaId}`);
                const data     = await response.json();

                if (data.success && data.sedes && data.sedes.length > 0) {
                    predSede.innerHTML = '<option value="">-- Seleccione una sede --</option>';
                    data.sedes.forEach(sedeObj => {
                        const option = document.createElement('option');
                        option.value                   = sedeObj.nombre;
                        option.textContent             = sedeObj.nombre;
                        option.dataset.codInterprise   = sedeObj.cod_interprise;
                        predSede.appendChild(option);
                    });
                } else {
                    predSede.innerHTML = '<option value="">No hay sedes disponibles</option>';
                }
            } catch (error) {
                console.error('Error al cargar sedes:', error);
                alert('Error al cargar sedes');
            }
        });

        predSede.addEventListener('change', async function () {
            const programaId = predPrograma.value;
            const sedeNombre = this.value;
            predFocalizacion.disabled  = !sedeNombre;
            predComplemento.disabled   = true;
            btnCargarEstudiantes.disabled = true;

            if (!sedeNombre) {
                predFocalizacion.innerHTML = '<option value="">-- Seleccione sede primero --</option>';
                return;
            }

            try {
                const response = await fetch(`/facturacion/api/get-focalizaciones-for-programa/?programa_id=${programaId}`);
                const data     = await response.json();

                if (data.focalizaciones && data.focalizaciones.length > 0) {
                    predFocalizacion.innerHTML = '<option value="">-- Seleccione una focalización --</option>';
                    data.focalizaciones.forEach(foc => {
                        const option       = document.createElement('option');
                        option.value       = foc;
                        option.textContent = foc;
                        predFocalizacion.appendChild(option);
                    });
                } else {
                    predFocalizacion.innerHTML = '<option value="">No hay focalizaciones disponibles</option>';
                }
            } catch (error) {
                console.error('Error al cargar focalizaciones:', error);
                alert('Error al cargar focalizaciones');
            }
        });

        predFocalizacion.addEventListener('change', function () {
            predComplemento.disabled = !this.value;
        });

        predComplemento.addEventListener('change', function () {
            btnCargarEstudiantes.disabled = !this.value;
        });

        btnCargarEstudiantes.addEventListener('click', async function () {
            const programaId  = predPrograma.value;
            const sedeNombre  = predSede.value;
            const focalizacion = predFocalizacion.value;
            const complemento  = predComplemento.value;

            if (!programaId || !sedeNombre || !focalizacion || !complemento) {
                alert('Complete todos los campos');
                return;
            }

            const originalText = this.innerHTML;
            this.disabled  = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cargando...';

            try {
                const url      = `/facturacion/api/conteo-estudiantes-por-nivel/?programa_id=${programaId}&sede_nombre=${encodeURIComponent(sedeNombre)}&focalizacion=${focalizacion}&complemento=${encodeURIComponent(complemento)}`;
                const response = await fetch(url);
                const data     = await response.json();

                if (data.success) {
                    conteoEstudiantes = {
                        total:        data.total,
                        preescolar:   data.por_nivel.preescolar,
                        primaria_1_3: data.por_nivel.primaria_1_3,
                        primaria_4_5: data.por_nivel.primaria_4_5,
                        secundaria:   data.por_nivel.secundaria,
                        media:        data.por_nivel.media
                    };

                    document.getElementById('count-preescolar').textContent   = conteoEstudiantes.preescolar;
                    document.getElementById('count-primaria-1-3').textContent  = conteoEstudiantes.primaria_1_3;
                    document.getElementById('count-primaria-4-5').textContent  = conteoEstudiantes.primaria_4_5;
                    document.getElementById('count-secundaria').textContent    = conteoEstudiantes.secundaria;
                    document.getElementById('count-media').textContent         = conteoEstudiantes.media;
                    document.getElementById('count-total').textContent         = conteoEstudiantes.total;

                    document.getElementById('info-estudiantes-container').style.display = 'block';
                    configuracionDias = [];
                    actualizarTablaDias();
                    actualizarTotales();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error al cargar estudiantes');
            } finally {
                this.disabled  = false;
                this.innerHTML = originalText;
            }
        });

        // Botón "Agregar Día": abre el calendario en modo prediligenciada
        const btnAgregarDia = document.getElementById('btn-agregar-dia');
        if (btnAgregarDia) {
            btnAgregarDia.addEventListener('click', function (e) {
                e.stopPropagation();

                // Toggle: si el popover ya está abierto en modo prediligenciada, cerrarlo
                if (calPopover.style.display === 'block' && calModoPrediligenciada) {
                    closeCalendar();
                    return;
                }

                // Abrir calendario en modo prediligenciada (sin hidden input ni botón activo)
                calModoPrediligenciada = true;
                calActiveBtn           = null;
                calActiveTarget        = null;
                calSelectedDays        = new Set();

                const mesNombre = document.getElementById('pred-mes')?.value || 'ENERO';
                renderCalendar(mesNombre, AÑO_ACTUAL);

                // Posicionar el popover relativo al botón (misma lógica que openCalendar)
                calPopover.style.visibility = 'hidden';
                calPopover.style.display    = 'block';

                const rect = this.getBoundingClientRect();
                const popW = calPopover.offsetWidth  || 280;
                const popH = calPopover.offsetHeight || 300;
                const vpW  = window.innerWidth;
                const vpH  = window.innerHeight;

                let left = rect.left;
                if (left + popW > vpW - 8) left = vpW - popW - 8;
                if (left < 8) left = 8;

                let top;
                if (rect.bottom + 6 + popH <= vpH) {
                    top = rect.bottom + 6;
                } else {
                    top = Math.max(8, rect.top - popH - 6);
                }

                calPopover.style.left       = left + 'px';
                calPopover.style.top        = top  + 'px';
                calPopover.style.visibility = 'visible';
            });
        }

        // Botón Aplicar del calendario: agrega los días seleccionados a configuracionDias
        const calBtnAplicar = document.getElementById('cal-btn-aplicar');
        if (calBtnAplicar) {
            calBtnAplicar.addEventListener('click', function () {
                if (calModoPrediligenciada && calSelectedDays.size > 0) {
                    calSelectedDays.forEach(dia => {
                        if (!configuracionDias.find(d => d.dia === dia)) {
                            configuracionDias.push({
                                dia, total: 0, preescolar: 0, primaria_1_3: 0,
                                primaria_4_5: 0, secundaria: 0, media: 0
                            });
                        }
                    });
                    configuracionDias.sort((a, b) => a.dia - b.dia);
                    actualizarTablaDias();
                    actualizarTotales();
                }
                closeCalendar();
            });
        }

        document.getElementById('btn-generar-prediligenciado').addEventListener('click', async function () {
            if (configuracionDias.length === 0) {
                alert('Configure al menos un día antes de generar');
                return;
            }

            const programaId         = predPrograma.value;
            const sedeNombre         = predSede.value;
            const selectedOption     = predSede.selectedOptions[0];
            const sedeCodInterprise  = selectedOption?.dataset.codInterprise;
            const focalizacion       = predFocalizacion.value;
            const complemento        = predComplemento.value;
            const mes                = document.getElementById('pred-mes').value;

            if (!sedeCodInterprise) {
                alert('Error: No se pudo obtener el código de la sede. Por favor, vuelva a seleccionar la sede.');
                return;
            }

            const originalText = this.innerHTML;
            this.disabled  = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generando PDF...';

            try {
                const response = await fetch('/facturacion/generar-asistencia-prediligenciada/', {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({
                        programa_id:        programaId,
                        sede_cod_interprise: sedeCodInterprise,
                        sede_nombre:        sedeNombre,
                        mes,
                        focalizacion,
                        complemento,
                        dias: configuracionDias
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
                }

                const blob        = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a           = document.createElement('a');
                a.style.display   = 'none';
                a.href            = downloadUrl;
                a.download        = `Asistencia_Prediligenciada_${sedeNombre.replace(/ /g, '_')}_${complemento.replace(/ /g, '_')}_${mes}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                document.body.removeChild(a);
                mostrarExito('¡PDF prediligenciado generado exitosamente!');
            } catch (error) {
                console.error('Error:', error);
                mostrarError(error.message);
            } finally {
                this.disabled  = false;
                this.innerHTML = originalText;
            }
        });
    }

    function actualizarTablaDias() {
        const tbody = document.getElementById('tabla-dias-body');

        if (configuracionDias.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align:center;color:#999;padding:30px;">
                        No hay días configurados. Haga clic en "Agregar Día" para empezar.
                    </td>
                </tr>`;
            document.getElementById('btn-generar-prediligenciado').disabled = true;
            return;
        }

        const fragment = document.createDocumentFragment();

        configuracionDias.forEach((config, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${config.dia}</strong></td>
                <td><strong id="total-dia-${index}">${config.total}</strong></td>
                <td><input type="number" min="0" max="${conteoEstudiantes.preescolar}"   value="${config.preescolar}"   data-index="${index}" data-nivel="preescolar"   class="input-nivel"></td>
                <td><input type="number" min="0" max="${conteoEstudiantes.primaria_1_3}" value="${config.primaria_1_3}" data-index="${index}" data-nivel="primaria_1_3" class="input-nivel"></td>
                <td><input type="number" min="0" max="${conteoEstudiantes.primaria_4_5}" value="${config.primaria_4_5}" data-index="${index}" data-nivel="primaria_4_5" class="input-nivel"></td>
                <td><input type="number" min="0" max="${conteoEstudiantes.secundaria}"   value="${config.secundaria}"   data-index="${index}" data-nivel="secundaria"   class="input-nivel"></td>
                <td><input type="number" min="0" max="${conteoEstudiantes.media}"        value="${config.media}"        data-index="${index}" data-nivel="media"        class="input-nivel"></td>
                <td>
                    <button type="button" class="btn-eliminar-dia" data-index="${index}">
                        <i class="fas fa-trash"></i> Eliminar
                    </button>
                </td>`;
            fragment.appendChild(tr);
        });

        tbody.innerHTML = '';
        tbody.appendChild(fragment);

        tbody.querySelectorAll('.input-nivel').forEach(input => {
            input.addEventListener('change', function () {
                const index = parseInt(this.dataset.index);
                const nivel = this.dataset.nivel;
                let valor   = parseInt(this.value) || 0;
                const max   = conteoEstudiantes[nivel];

                if (valor > max) { alert(`No puede exceder ${max} estudiantes de ${nivel}`); valor = max; this.value = max; }
                if (valor < 0)   { valor = 0; this.value = 0; }

                configuracionDias[index][nivel] = valor;
                configuracionDias[index].total  =
                    configuracionDias[index].preescolar +
                    configuracionDias[index].primaria_1_3 +
                    configuracionDias[index].primaria_4_5 +
                    configuracionDias[index].secundaria +
                    configuracionDias[index].media;

                document.getElementById(`total-dia-${index}`).textContent = configuracionDias[index].total;
                actualizarTotales();
            });
        });

        tbody.querySelectorAll('.btn-eliminar-dia').forEach(btn => {
            btn.addEventListener('click', function () {
                configuracionDias.splice(parseInt(this.dataset.index), 1);
                actualizarTablaDias();
                actualizarTotales();
            });
        });

        document.getElementById('btn-generar-prediligenciado').disabled = false;
    }

    function actualizarTotales() {
        const totales = { preescolar: 0, primaria_1_3: 0, primaria_4_5: 0, secundaria: 0, media: 0, general: 0 };

        configuracionDias.forEach(config => {
            totales.preescolar   += config.preescolar;
            totales.primaria_1_3 += config.primaria_1_3;
            totales.primaria_4_5 += config.primaria_4_5;
            totales.secundaria   += config.secundaria;
            totales.media        += config.media;
            totales.general      += config.total;
        });

        ['preescolar', 'primaria_1_3', 'primaria_4_5', 'secundaria', 'media'].forEach(nivel => {
            const elem = document.getElementById(`total-${nivel.replace(/_/g, '-')}`);
            if (elem) {
                elem.textContent   = totales[nivel];
                elem.style.color   = totales[nivel] > conteoEstudiantes[nivel] ? 'red' : '';
            }
        });

        const elemGeneral = document.getElementById('total-general');
        if (elemGeneral) {
            elemGeneral.textContent = totales.general;
            elemGeneral.style.color = totales.general > conteoEstudiantes.total ? 'red' : '';
        }
    }

    // ===== GENERACIÓN INDIVIDUAL POR SEDE =====
    document.addEventListener('click', async function (e) {
        if (!e.target.classList.contains('btn-generar-asistencia') &&
            !e.target.closest('.btn-generar-asistencia')) return;

        e.preventDefault();

        const button    = e.target.classList.contains('btn-generar-asistencia')
            ? e.target
            : e.target.closest('.btn-generar-asistencia');
        const originalText = button.innerHTML;

        try {
            const sedeCod    = button.dataset.sedeCod;
            const programaId = button.dataset.programaId;

            if (!sedeCod || !programaId) {
                alert('Error: No se pudo obtener el código de la sede o el ID del programa.');
                return;
            }

            const mesElement          = document.getElementById(`mes-${sedeCod}`);
            const focalizacionElement = document.getElementById(`focalizacion-${sedeCod}`);
            const diasElement         = document.getElementById(`dias-${sedeCod}`);

            if (!mesElement || !focalizacionElement || !diasElement) {
                alert(`Error: No se encontraron los selectores para la sede ${sedeCod}`);
                return;
            }

            const mes          = mesElement.value;
            const focalizacion = focalizacionElement.value;
            const dias         = diasElement.value.trim();

            if (!mes || !focalizacion) {
                alert('Error: Faltan parámetros (mes o focalización)');
                return;
            }

            button.disabled  = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Generando...`;

            let url = `/facturacion/generar-asistencia/${programaId}/${sedeCod}/${mes}/${focalizacion}/`;
            if (dias) url += `?${new URLSearchParams({ dias }).toString()}`;

            await descargarArchivo(url, button, originalText);

        } catch (error) {
            mostrarError(error.message);
            button.disabled  = false;
            button.innerHTML = originalText;
        }
    });

    // ===== GENERACIÓN MASIVA POR PROGRAMA =====
    const btnGenerarMasivo = document.getElementById('btn-generar-masivo');
    if (btnGenerarMasivo) {
        btnGenerarMasivo.addEventListener('click', async function (e) {
            e.preventDefault();

            const programaId    = this.dataset.programaId;
            const programaNombre = this.dataset.programaNombre || '';
            const mes            = document.getElementById('bulk-mes').value;
            const focalizacion   = document.getElementById('bulk-focalizacion').value;
            const dias           = document.getElementById('bulk-dias').value.trim();

            if (!programaId || !mes || !focalizacion) {
                alert('Error: Faltan parámetros para la generación masiva.');
                return;
            }

            let confirmacionMsg =
                `¿Está seguro de generar reportes para TODAS las sedes del programa "${programaNombre}" con los parámetros:\n\n` +
                `• Mes: ${mes}\n` +
                `• Focalización: ${focalizacion}\n`;
            if (dias) confirmacionMsg += `• Días específicos: ${dias}\n`;
            confirmacionMsg += `\nEsta operación puede tomar varios minutos.`;

            if (!confirm(confirmacionMsg)) return;

            const originalText = this.innerHTML;

            try {
                this.disabled  = true;
                this.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Generando ZIP Masivo... Por favor espere`;

                let url = `/facturacion/generar-zip-masivo/${programaId}/${mes}/${encodeURIComponent(focalizacion)}/`;
                if (dias) url += `?${new URLSearchParams({ dias }).toString()}`;

                await descargarArchivo(url, this, originalText);
            } catch (error) {
                mostrarError(error.message);
                this.disabled  = false;
                this.innerHTML = originalText;
            }
        });
    }

    // ===== FUNCIONES AUXILIARES =====
    async function descargarArchivo(url, button, originalText) {
        const response = await fetch(url, {
            method:  'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || (!contentType.includes('application/zip') && !contentType.includes('application/pdf'))) {
            throw new Error('La respuesta del servidor no es un archivo válido (PDF o ZIP)');
        }

        const blob        = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);

        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'reporte.zip';
        if (contentDisposition) {
            const match = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
            if (match && match[1]) filename = match[1].replace(/['"]/g, '');
        }

        const a         = document.createElement('a');
        a.style.display = 'none';
        a.href          = downloadUrl;
        a.download      = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        mostrarExito('¡Reporte generado exitosamente!');
        button.disabled  = false;
        button.innerHTML = originalText;
    }

    function mostrarExito(mensaje) {
        window.showNotification ? window.showNotification(mensaje, 'success') : alert(mensaje);
    }

    function mostrarError(mensaje) {
        window.showNotification ? window.showNotification(`Error: ${mensaje}`, 'error') : alert(`Error: ${mensaje}`);
    }
});
