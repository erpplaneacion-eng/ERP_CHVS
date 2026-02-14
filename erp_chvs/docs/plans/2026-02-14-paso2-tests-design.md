# Diseno de Tests Integracion Paso 2

## Objetivo
Cubrir con tests de integracion backend lo descrito en `erp_chvs/PASO2_README.md` para:
- `vista_preparaciones_editor`
- `api_guardar_ingredientes_por_nivel`

## Alcance
- Validar estructura de datos por nivel escolar.
- Validar creacion automatica de `TablaAnalisisNutricionalMenu` por nivel.
- Validar filtrado de rangos `MinutaPatronMeta` por modalidad + nivel.
- Validar guardado de pesos por nivel, calculo nutricional y recalculo de totales.
- Validar errores de contrato del endpoint (`GET`, payload vacio, analisis inexistente).

## Enfoque
Suite de integracion con `django.test.Client` y rutas reales.

## Casos
1. `test_vista_preparaciones_editor_crea_analisis_por_nivel_y_aplica_rangos_por_nivel`
2. `test_api_guardar_ingredientes_por_nivel_guarda_registros_y_recalcula_totales`
3. `test_api_guardar_ingredientes_por_nivel_rechaza_metodo_get`
4. `test_api_guardar_ingredientes_por_nivel_valida_payload_vacio`
5. `test_api_guardar_ingredientes_por_nivel_reporta_analisis_no_encontrado`

## Datos de prueba
- 2 niveles escolares (`prescolar`, `primaria`)
- 1 modalidad, 1 programa, 1 menu
- 1 componente/grupo
- 1 alimento ICBF + 1 ingrediente Siesa (mismo codigo)
- 1 preparacion con 1 relacion de ingrediente
- 2 metas de minuta (min/max distintos por nivel)
- 2 requerimientos nutricionales (uno por nivel)

## Notas
Durante la ejecucion se detectaron y corrigieron defectos existentes en `nutricion/views.py` para alinear implementacion y contrato de Paso 2.
