/**
 * Módulo de Guardado Automático
 * Responsable de persistir los cambios del análisis nutricional al servidor
 */

const GuardadoAutomatico = {
    /**
     * Guarda automáticamente el análisis nutricional editado
     * Se ejecuta después de cada cambio en pesos o porcentajes
     *
     * @param {number} nivelIndex - Índice del nivel escolar
     * @param {number} menuId - ID del menú
     */
    async guardarAnalisis(nivelIndex, menuId) {
        // Validar dependencias
        if (!window.NutricionState) {
            console.error('❌ [GuardadoAutomatico] window.NutricionState no está disponible');
            return;
        }
        if (!window.NutricionUtils) {
            console.error('❌ [GuardadoAutomatico] window.NutricionUtils no está disponible');
            return;
        }

        try {
            // Recopilar totales actuales del nivel
            const totales = {
                calorias: parseFloat(document.getElementById(`nivel-${nivelIndex}-calorias`).textContent.replace(' Kcal', '')) || 0,
                proteina: parseFloat(document.getElementById(`nivel-${nivelIndex}-proteina`).textContent.replace(' g', '')) || 0,
                grasa: parseFloat(document.getElementById(`nivel-${nivelIndex}-grasa`).textContent.replace(' g', '')) || 0,
                cho: parseFloat(document.getElementById(`nivel-${nivelIndex}-cho`).textContent.replace(' g', '')) || 0,
                calcio: parseFloat(document.getElementById(`nivel-${nivelIndex}-calcio`).textContent.replace(' mg', '')) || 0,
                hierro: parseFloat(document.getElementById(`nivel-${nivelIndex}-hierro`).textContent.replace(' mg', '')) || 0,
                sodio: parseFloat(document.getElementById(`nivel-${nivelIndex}-sodio`).textContent.replace(' mg', '')) || 0,
                peso_neto: 0,  // Se calculará sumando ingredientes
                peso_bruto: 0  // Se calculará sumando ingredientes
            };

            // Recopilar porcentajes de adecuación
            const porcentajes = {
                calorias: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calorias"]`).value) || 0,
                proteina: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="proteina"]`).value) || 0,
                grasa: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="grasa"]`).value) || 0,
                cho: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="cho"]`).value) || 0,
                calcio: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calcio"]`).value) || 0,
                hierro: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="hierro"]`).value) || 0,
                sodio: parseFloat(document.querySelector(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="sodio"]`).value) || 0
            };

            // Recopilar datos de ingredientes configurados
            const ingredientes = [];
            const ingredienteRows = document.querySelectorAll(`.ingrediente-row[data-nivel="${nivelIndex}"]`);

            ingredienteRows.forEach(row => {
                const prepIndex = row.dataset.prep;
                const ingIndex = row.dataset.ing;
                const pesoInput = row.querySelector('.peso-input');

                // Obtener IDs reales desde data attributes
                const prepIdReal = row.dataset.prepId || pesoInput.dataset.prepId;
                const ingIdReal = row.dataset.ingId || pesoInput.dataset.ingId;

                console.log(`[DEBUG] Guardando ingrediente - Índices: prep=${prepIndex}, ing=${ingIndex}, IDs reales: prepId=${prepIdReal}, ingId=${ingIdReal}`);

                const pesoNeto = parseFloat(pesoInput.value) || 0;
                const pesoBruto = parseFloat(document.getElementById(`bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0;

                const ingrediente = {
                    id_preparacion: prepIdReal,
                    id_ingrediente_siesa: ingIdReal,
                    peso_neto: pesoNeto,
                    peso_bruto: pesoBruto,
                    calorias: parseFloat(document.getElementById(`cal-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    proteina: parseFloat(document.getElementById(`prot-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    grasa: parseFloat(document.getElementById(`grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    cho: parseFloat(document.getElementById(`cho-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    calcio: parseFloat(document.getElementById(`calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    hierro: parseFloat(document.getElementById(`hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0,
                    sodio: parseFloat(document.getElementById(`sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).textContent) || 0
                };

                // Acumular pesos totales
                totales.peso_neto += pesoNeto;
                totales.peso_bruto += pesoBruto;

                ingredientes.push(ingrediente);
            });

            // Obtener ID del nivel escolar desde los datos almacenados
            const idNivelEscolar = window.NutricionState.datosNutricionales &&
                                  window.NutricionState.datosNutricionales.analisis_por_nivel &&
                                  window.NutricionState.datosNutricionales.analisis_por_nivel[nivelIndex] &&
                                  window.NutricionState.datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar &&
                                  window.NutricionState.datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar.id;

            console.log('[DEBUG] ID Nivel Escolar obtenido:', {
                nivelIndex,
                idNivelEscolar,
                nivel_escolar_completo: window.NutricionState.datosNutricionales?.analisis_por_nivel?.[nivelIndex]?.nivel_escolar,
                existe_datos: !!window.NutricionState.datosNutricionales
            });

            if (!idNivelEscolar || idNivelEscolar === '-1' || idNivelEscolar === -1) {
                console.error('ID de nivel escolar inválido:', idNivelEscolar);
                console.error('Datos completos:', window.NutricionState.datosNutricionales?.analisis_por_nivel?.[nivelIndex]);
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
};

// Exponer globalmente para compatibilidad con código legacy
window.GuardadoAutomatico = GuardadoAutomatico;
window.guardarAnalisisAutomatico = GuardadoAutomatico.guardarAnalisis.bind(GuardadoAutomatico);
