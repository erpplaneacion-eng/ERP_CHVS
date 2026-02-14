# Diseno de Tests Integracion Paso 5

## Objetivo
Validar por contrato lo descrito en `erp_chvs/PASO5_README.md` para funciones auxiliares de optimizacion.

## Alcance
- Template: toolbar de nivel y panel de sugerencias.
- JavaScript: funciones principales de paso 5 y event delegation de botones.

## Enfoque
- Pruebas de contrato (sin browser real) sobre render de `preparaciones_editor` y sobre contenido de `preparaciones_editor.js`.

## Casos implementados
1. `test_paso5_template_incluye_toolbar_de_optimizacion_por_nivel`
2. `test_paso5_template_incluye_panel_sugerencias_oculto`
3. `test_paso5_js_contiene_funciones_auxiliares_de_optimizacion`
4. `test_paso5_js_contiene_event_delegation_y_placeholder_optimizacion`

## Resultado
La suite `nutricion.tests_paso2_preparaciones_editor` queda en 13 tests en verde (PASO 2 + PASO 4 + PASO 5).
